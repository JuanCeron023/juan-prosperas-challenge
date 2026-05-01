"""Unit tests for the job service."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.jobs.service import create_job, get_job, list_user_jobs


class TestCreateJob:
    """Tests for create_job function."""

    @patch("app.jobs.service.publish_job_message")
    @patch("app.jobs.service.db_create_job")
    def test_create_job_returns_pending(self, mock_db_create, mock_publish):
        """create_job returns a dict with job_id and status PENDING."""
        mock_db_create.return_value = {"job_id": "test-id", "status": "PENDING"}

        result = create_job(
            user_id="user-123",
            report_type="sales",
            date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            format="csv",
            priority="standard",
        )

        assert result["status"] == "PENDING"
        assert "job_id" in result

    @patch("app.jobs.service.publish_job_message")
    @patch("app.jobs.service.db_create_job")
    def test_create_job_publishes_to_sqs(self, mock_db_create, mock_publish):
        """create_job calls publish_job_message with correct parameters."""
        mock_db_create.return_value = {"job_id": "test-id", "status": "PENDING"}

        create_job(
            user_id="user-123",
            report_type="inventory",
            date_range={"start_date": "2024-02-01", "end_date": "2024-02-28"},
            format="pdf",
            priority="high",
        )

        mock_publish.assert_called_once()
        call_kwargs = mock_publish.call_args[1]
        assert call_kwargs["user_id"] == "user-123"
        assert call_kwargs["report_type"] == "inventory"
        assert call_kwargs["format"] == "pdf"
        assert call_kwargs["priority"] == "high"

    @patch("app.jobs.service.update_job_status")
    @patch("app.jobs.service.publish_job_message")
    @patch("app.jobs.service.db_create_job")
    def test_create_job_sqs_failure_marks_failed(
        self, mock_db_create, mock_publish, mock_update
    ):
        """When SQS publish fails, the job is marked FAILED and 503 is raised."""
        mock_db_create.return_value = {"job_id": "test-id", "status": "PENDING"}
        mock_publish.side_effect = Exception("SQS connection refused")

        with pytest.raises(HTTPException) as exc_info:
            create_job(
                user_id="user-123",
                report_type="sales",
                date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"},
                format="csv",
            )

        assert exc_info.value.status_code == 503
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0]
        assert call_args[1] == "FAILED"


class TestGetJob:
    """Tests for get_job function."""

    @patch("app.jobs.service.db_get_job")
    def test_get_job_returns_job_for_owner(self, mock_db_get):
        """get_job returns the job when the requesting user is the owner."""
        mock_db_get.return_value = {
            "job_id": "job-1",
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }

        result = get_job("job-1", "user-123")

        assert result["job_id"] == "job-1"
        assert result["user_id"] == "user-123"

    @patch("app.jobs.service.db_get_job")
    def test_get_job_raises_403_for_non_owner(self, mock_db_get):
        """get_job raises 403 when the requesting user is not the owner."""
        mock_db_get.return_value = {
            "job_id": "job-1",
            "user_id": "user-123",
            "status": "PENDING",
        }

        with pytest.raises(HTTPException) as exc_info:
            get_job("job-1", "user-other")

        assert exc_info.value.status_code == 403

    @patch("app.jobs.service.db_get_job")
    def test_get_job_raises_404_for_missing(self, mock_db_get):
        """get_job raises 404 when the job does not exist."""
        mock_db_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_job("nonexistent-id", "user-123")

        assert exc_info.value.status_code == 404


class TestListUserJobs:
    """Tests for list_user_jobs function."""

    @patch("app.jobs.service.db_list_jobs_by_user")
    def test_list_user_jobs_returns_paginated(self, mock_db_list):
        """list_user_jobs returns paginated results with metadata."""
        mock_db_list.return_value = {
            "items": [
                {"job_id": "job-1", "user_id": "user-123", "status": "PENDING"},
                {"job_id": "job-2", "user_id": "user-123", "status": "COMPLETED"},
            ],
            "total": 5,
            "next_cursor": "cursor-abc",
        }

        result = list_user_jobs("user-123", page=1, limit=2)

        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["next_cursor"] == "cursor-abc"
