"""Unit tests for the health check endpoint."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200_when_all_services_healthy(self, client):
        """Health check returns 200 with healthy status when DynamoDB and SQS are reachable."""
        mock_table = MagicMock()
        mock_table.table_status = "ACTIVE"

        mock_sqs = MagicMock()
        mock_sqs.get_queue_attributes.return_value = {
            "Attributes": {"ApproximateNumberOfMessages": "0"}
        }

        with patch(
            "backend.app.db.client.get_dynamodb_table", return_value=mock_table
        ), patch("backend.app.queue.client.get_sqs_client", return_value=mock_sqs):
            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["dynamodb"] == "ok"
        assert body["sqs"] == "ok"
        assert "metrics" in body

    def test_health_returns_503_when_dynamodb_fails(self, client):
        """Health check returns 503 when DynamoDB is unreachable."""
        mock_sqs = MagicMock()
        mock_sqs.get_queue_attributes.return_value = {
            "Attributes": {"ApproximateNumberOfMessages": "0"}
        }

        with patch(
            "backend.app.db.client.get_dynamodb_table",
            side_effect=Exception("DynamoDB unreachable"),
        ), patch("backend.app.queue.client.get_sqs_client", return_value=mock_sqs):
            response = client.get("/health")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "unhealthy"
        assert body["dynamodb"] == "error"
        assert body["sqs"] == "ok"

    def test_health_returns_503_when_sqs_fails(self, client):
        """Health check returns 503 when SQS is unreachable."""
        mock_table = MagicMock()
        mock_table.table_status = "ACTIVE"

        mock_sqs = MagicMock()
        mock_sqs.get_queue_attributes.side_effect = Exception("SQS unreachable")

        with patch(
            "backend.app.db.client.get_dynamodb_table", return_value=mock_table
        ), patch("backend.app.queue.client.get_sqs_client", return_value=mock_sqs):
            response = client.get("/health")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "unhealthy"
        assert body["dynamodb"] == "ok"
        assert body["sqs"] == "error"

    def test_health_returns_503_when_both_services_fail(self, client):
        """Health check returns 503 when both DynamoDB and SQS are unreachable."""
        mock_sqs = MagicMock()
        mock_sqs.get_queue_attributes.side_effect = Exception("SQS unreachable")

        with patch(
            "backend.app.db.client.get_dynamodb_table",
            side_effect=Exception("DynamoDB unreachable"),
        ), patch("backend.app.queue.client.get_sqs_client", return_value=mock_sqs):
            response = client.get("/health")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "unhealthy"
        assert body["dynamodb"] == "error"
        assert body["sqs"] == "error"

    def test_health_includes_metrics(self, client):
        """Health check response includes metrics data."""
        mock_table = MagicMock()
        mock_table.table_status = "ACTIVE"

        mock_sqs = MagicMock()
        mock_sqs.get_queue_attributes.return_value = {
            "Attributes": {"ApproximateNumberOfMessages": "0"}
        }

        with patch(
            "backend.app.db.client.get_dynamodb_table", return_value=mock_table
        ), patch("backend.app.queue.client.get_sqs_client", return_value=mock_sqs):
            response = client.get("/health")

        body = response.json()
        assert "metrics" in body
        metrics = body["metrics"]
        assert "jobs_created" in metrics
        assert "jobs_completed" in metrics
        assert "jobs_failed" in metrics
        assert "avg_processing_time_seconds" in metrics

    def test_health_does_not_require_authentication(self, client):
        """Health check endpoint is accessible without JWT token."""
        mock_table = MagicMock()
        mock_table.table_status = "ACTIVE"

        mock_sqs = MagicMock()
        mock_sqs.get_queue_attributes.return_value = {
            "Attributes": {"ApproximateNumberOfMessages": "0"}
        }

        with patch(
            "backend.app.db.client.get_dynamodb_table", return_value=mock_table
        ), patch("backend.app.queue.client.get_sqs_client", return_value=mock_sqs):
            # No Authorization header
            response = client.get("/health")

        assert response.status_code == 200
