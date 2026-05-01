"""Integration test for the full job lifecycle.

Tests the complete flow: create job → verify PENDING → simulate worker update → verify COMPLETED.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.auth.service import create_access_token
from app.main import app


@pytest.fixture
def auth_token():
    """Create a valid JWT token for testing."""
    with patch("app.auth.service.settings") as mock_settings:
        mock_settings.jwt_secret = "test-secret"
        mock_settings.jwt_expiration_minutes = 60
        token = create_access_token("user-integration-test", "testuser")
    return token


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


@mock_aws
class TestFullJobLifecycle:
    """Integration test for the complete job lifecycle."""

    def _setup_aws_resources(self):
        """Set up mocked AWS resources (DynamoDB table and SQS queues)."""
        # Create DynamoDB table
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

        # Create SQS queues
        sqs = boto3.client("sqs", region_name="us-east-1")
        standard_queue = sqs.create_queue(QueueName="reports-queue-standard")
        high_queue = sqs.create_queue(QueueName="reports-queue-high")

        return dynamodb, sqs, standard_queue["QueueUrl"], high_queue["QueueUrl"]

    def test_full_job_lifecycle(self, client):
        """Test complete flow: create → PENDING → worker update → COMPLETED."""
        dynamodb, sqs, standard_url, high_url = self._setup_aws_resources()
        table = dynamodb.Table("jobs")

        with patch("app.auth.service.settings") as mock_auth_settings, \
             patch("app.db.repository._get_jobs_table", return_value=table), \
             patch("app.queue.publisher.get_sqs_client", return_value=sqs), \
             patch("app.queue.publisher.settings") as mock_pub_settings:

            mock_auth_settings.jwt_secret = "test-secret"
            mock_auth_settings.jwt_expiration_minutes = 60
            mock_pub_settings.sqs_standard_queue_url = standard_url
            mock_pub_settings.sqs_high_queue_url = high_url

            token = create_access_token("user-lifecycle", "lifecycleuser")

            # Step 1: Create a job
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

            assert response.status_code == 201
            job_data = response.json()
            assert job_data["status"] == "PENDING"
            job_id = job_data["job_id"]

            # Step 2: Verify job is PENDING
            with patch("app.auth.service.settings") as mock_auth2:
                mock_auth2.jwt_secret = "test-secret"
                mock_auth2.jwt_expiration_minutes = 60

                response = client.get(
                    f"/jobs/{job_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 200
            assert response.json()["status"] == "PENDING"

            # Step 3: Simulate worker updating job to COMPLETED
            from app.db.repository import update_job_status

            update_job_status(
                job_id, "COMPLETED", result_url="https://s3.example.com/report.csv"
            )

            # Step 4: Verify job is COMPLETED
            with patch("app.auth.service.settings") as mock_auth3:
                mock_auth3.jwt_secret = "test-secret"
                mock_auth3.jwt_expiration_minutes = 60

                response = client.get(
                    f"/jobs/{job_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "COMPLETED"
            assert result["result_url"] == "https://s3.example.com/report.csv"
