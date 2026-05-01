"""Unit tests for the DynamoDB job repository."""

import uuid
from unittest.mock import patch

import pytest
from moto import mock_aws

from app.db.repository import (
    create_job,
    get_job,
    list_jobs_by_user,
    update_job_status,
)


@pytest.fixture
def mock_table(dynamodb_resource):
    """Patch the repository to use the mocked DynamoDB table."""
    table = dynamodb_resource.Table("jobs")
    with patch("app.db.repository._get_jobs_table", return_value=table):
        yield table


@mock_aws
class TestCreateJob:
    """Tests for create_job function."""

    def test_creates_job_with_all_fields(self, mock_table):
        job_data = {
            "job_id": str(uuid.uuid4()),
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "format": "csv",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        }

        result = create_job(job_data)

        assert result["job_id"] == job_data["job_id"]
        assert result["user_id"] == "user-123"
        assert result["status"] == "PENDING"
        assert result["report_type"] == "sales"
        assert "created_at" in result
        assert "updated_at" in result
        assert result["created_at"] == result["updated_at"]

    def test_sets_timestamps_automatically(self, mock_table):
        job_data = {
            "job_id": str(uuid.uuid4()),
            "user_id": "user-456",
            "status": "PENDING",
            "report_type": "inventory",
            "format": "pdf",
            "priority": "high",
            "date_range": {"start_date": "2024-02-01", "end_date": "2024-02-28"},
        }

        result = create_job(job_data)

        # Timestamps should be ISO 8601 format
        assert "T" in result["created_at"]
        assert "+" in result["created_at"] or "Z" in result["created_at"]

    def test_excludes_none_values(self, mock_table):
        job_data = {
            "job_id": str(uuid.uuid4()),
            "user_id": "user-789",
            "status": "PENDING",
            "report_type": "analytics",
            "format": "json",
            "priority": "standard",
            "date_range": {"start_date": "2024-03-01", "end_date": "2024-03-31"},
            "result_url": None,
            "error_message": None,
        }

        result = create_job(job_data)

        assert "result_url" not in result
        assert "error_message" not in result


@mock_aws
class TestGetJob:
    """Tests for get_job function."""

    def test_returns_existing_job(self, mock_table):
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "format": "csv",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        }
        create_job(job_data)

        result = get_job(job_id)

        assert result is not None
        assert result["job_id"] == job_id
        assert result["user_id"] == "user-123"

    def test_returns_none_for_nonexistent_job(self, mock_table):
        result = get_job("nonexistent-id")
        assert result is None


@mock_aws
class TestUpdateJobStatus:
    """Tests for update_job_status function."""

    def test_updates_status(self, mock_table):
        job_id = str(uuid.uuid4())
        create_job({
            "job_id": job_id,
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "format": "csv",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        })

        result = update_job_status(job_id, "PROCESSING")

        assert result["status"] == "PROCESSING"
        assert result["job_id"] == job_id

    def test_updates_updated_at_timestamp(self, mock_table):
        job_id = str(uuid.uuid4())
        created = create_job({
            "job_id": job_id,
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "format": "csv",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        })

        result = update_job_status(job_id, "COMPLETED", result_url="https://example.com/report.csv")

        assert result["updated_at"] >= created["updated_at"]

    def test_sets_result_url_on_completed(self, mock_table):
        job_id = str(uuid.uuid4())
        create_job({
            "job_id": job_id,
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "format": "csv",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        })

        result = update_job_status(job_id, "COMPLETED", result_url="https://s3.example.com/report.csv")

        assert result["result_url"] == "https://s3.example.com/report.csv"

    def test_sets_error_message_on_failed(self, mock_table):
        job_id = str(uuid.uuid4())
        create_job({
            "job_id": job_id,
            "user_id": "user-123",
            "status": "PENDING",
            "report_type": "sales",
            "format": "csv",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        })

        result = update_job_status(job_id, "FAILED", error_message="Timeout during generation")

        assert result["error_message"] == "Timeout during generation"


@mock_aws
class TestListJobsByUser:
    """Tests for list_jobs_by_user function."""

    def test_returns_only_user_jobs(self, mock_table):
        # Create jobs for two different users
        for i in range(3):
            create_job({
                "job_id": str(uuid.uuid4()),
                "user_id": "user-A",
                "status": "PENDING",
                "report_type": "sales",
                "format": "csv",
                "priority": "standard",
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            })
        create_job({
            "job_id": str(uuid.uuid4()),
            "user_id": "user-B",
            "status": "PENDING",
            "report_type": "inventory",
            "format": "pdf",
            "priority": "standard",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        })

        result = list_jobs_by_user("user-A")

        assert result["total"] == 3
        assert len(result["items"]) == 3
        for item in result["items"]:
            assert item["user_id"] == "user-A"

    def test_returns_empty_for_user_with_no_jobs(self, mock_table):
        result = list_jobs_by_user("user-no-jobs")

        assert result["total"] == 0
        assert result["items"] == []
        assert result["next_cursor"] is None

    def test_respects_limit_parameter(self, mock_table):
        for i in range(5):
            create_job({
                "job_id": str(uuid.uuid4()),
                "user_id": "user-C",
                "status": "PENDING",
                "report_type": "sales",
                "format": "csv",
                "priority": "standard",
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            })

        result = list_jobs_by_user("user-C", limit=2)

        assert len(result["items"]) == 2
        assert result["total"] == 5
        assert result["next_cursor"] is not None

    def test_response_structure(self, mock_table):
        create_job({
            "job_id": str(uuid.uuid4()),
            "user_id": "user-D",
            "status": "PENDING",
            "report_type": "analytics",
            "format": "json",
            "priority": "high",
            "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        })

        result = list_jobs_by_user("user-D")

        assert "items" in result
        assert "total" in result
        assert "next_cursor" in result
