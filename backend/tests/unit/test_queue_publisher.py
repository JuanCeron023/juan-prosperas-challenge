"""Unit tests for the SQS queue publisher."""

import json
from unittest.mock import MagicMock, patch

from app.queue.publisher import publish_job_message


class TestPublishJobMessage:
    """Tests for publish_job_message function."""

    @patch("app.queue.publisher.get_sqs_client")
    @patch("app.queue.publisher.settings")
    def test_publish_standard_priority(self, mock_settings, mock_get_client):
        """Standard priority messages are sent to the standard queue."""
        mock_settings.sqs_standard_queue_url = "http://localhost:4566/000000000000/reports-queue-standard"
        mock_settings.sqs_high_queue_url = "http://localhost:4566/000000000000/reports-queue-high"

        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        mock_get_client.return_value = mock_sqs

        publish_job_message(
            job_id="job-1",
            user_id="user-1",
            report_type="sales",
            date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            format="csv",
            priority="standard",
        )

        mock_sqs.send_message.assert_called_once()
        call_kwargs = mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == "http://localhost:4566/000000000000/reports-queue-standard"

    @patch("app.queue.publisher.get_sqs_client")
    @patch("app.queue.publisher.settings")
    def test_publish_high_priority(self, mock_settings, mock_get_client):
        """High priority messages are sent to the high priority queue."""
        mock_settings.sqs_standard_queue_url = "http://localhost:4566/000000000000/reports-queue-standard"
        mock_settings.sqs_high_queue_url = "http://localhost:4566/000000000000/reports-queue-high"

        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-456"}
        mock_get_client.return_value = mock_sqs

        publish_job_message(
            job_id="job-2",
            user_id="user-2",
            report_type="inventory",
            date_range={"start_date": "2024-02-01", "end_date": "2024-02-28"},
            format="pdf",
            priority="high",
        )

        mock_sqs.send_message.assert_called_once()
        call_kwargs = mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == "http://localhost:4566/000000000000/reports-queue-high"

    @patch("app.queue.publisher.get_sqs_client")
    @patch("app.queue.publisher.settings")
    def test_message_contains_all_fields(self, mock_settings, mock_get_client):
        """The published message body contains all required fields."""
        mock_settings.sqs_standard_queue_url = "http://localhost:4566/000000000000/reports-queue-standard"
        mock_settings.sqs_high_queue_url = "http://localhost:4566/000000000000/reports-queue-high"

        mock_sqs = MagicMock()
        mock_sqs.send_message.return_value = {"MessageId": "msg-789"}
        mock_get_client.return_value = mock_sqs

        publish_job_message(
            job_id="job-3",
            user_id="user-3",
            report_type="analytics",
            date_range={"start_date": "2024-03-01", "end_date": "2024-03-31"},
            format="json",
            priority="standard",
        )

        call_kwargs = mock_sqs.send_message.call_args[1]
        message_body = json.loads(call_kwargs["MessageBody"])

        assert message_body["job_id"] == "job-3"
        assert message_body["user_id"] == "user-3"
        assert message_body["report_type"] == "analytics"
        assert message_body["date_range"] == {"start_date": "2024-03-01", "end_date": "2024-03-31"}
        assert message_body["format"] == "json"
        assert message_body["priority"] == "standard"
