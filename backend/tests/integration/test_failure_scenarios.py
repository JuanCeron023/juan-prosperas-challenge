"""Integration tests for failure scenarios.

Tests system behavior when SQS or DynamoDB are unavailable.
"""

from unittest.mock import MagicMock, patch

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.auth.service import create_access_token
from app.main import app


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


class TestSQSUnavailable:
    """Tests for when SQS is unavailable."""

    @mock_aws
    def test_sqs_unavailable_returns_503(self, client):
        """When SQS is down, creating a job returns 503."""
        # Set up DynamoDB (working)
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "job_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user-jobs-index",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )
        table = dynamodb.Table("jobs")

        # Mock SQS to raise an exception (simulating SQS being down)
        mock_sqs = MagicMock()
        mock_sqs.send_message.side_effect = Exception("SQS service unavailable")

        with patch("app.auth.service.settings") as mock_auth_settings, \
             patch("app.db.repository._get_jobs_table", return_value=table), \
             patch("app.queue.publisher.get_sqs_client", return_value=mock_sqs), \
             patch("app.queue.publisher.settings") as mock_pub_settings:

            mock_auth_settings.jwt_secret = "test-secret"
            mock_auth_settings.jwt_expiration_minutes = 60
            mock_pub_settings.sqs_standard_queue_url = "http://localhost:4566/000000000000/reports-queue-standard"
            mock_pub_settings.sqs_high_queue_url = "http://localhost:4566/000000000000/reports-queue-high"

            token = create_access_token("user-sqs-fail", "sqsfailuser")

            response = client.post(
                "/jobs",
                json={
                    "report_type": "sales",
                    "date_range": {
                        "start_date": "2024-01-01",
                        "end_date": "2024-01-31",
                    },
                    "format": "csv",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 503
            assert "enqueue" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower()


class TestDynamoDBUnavailable:
    """Tests for when DynamoDB is unavailable."""

    def test_dynamodb_unavailable_returns_500(self):
        """When DynamoDB is down, creating a job returns 500."""
        # Use raise_server_exceptions=False so the generic exception handler
        # can return a 500 response instead of propagating the exception.
        test_client = TestClient(app, raise_server_exceptions=False)

        # Mock DynamoDB table to raise an exception
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB service unavailable")

        with patch("app.auth.service.settings") as mock_auth_settings, \
             patch("app.db.repository._get_jobs_table", return_value=mock_table):

            mock_auth_settings.jwt_secret = "test-secret"
            mock_auth_settings.jwt_expiration_minutes = 60

            token = create_access_token("user-db-fail", "dbfailuser")

            response = test_client.post(
                "/jobs",
                json={
                    "report_type": "analytics",
                    "date_range": {
                        "start_date": "2024-01-01",
                        "end_date": "2024-01-31",
                    },
                    "format": "json",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 500
