"""SQS message publisher for job processing.

Publishes job messages to the appropriate SQS queue based on priority.
"""

import json
import logging

from backend.app.config import settings
from backend.app.queue.client import get_sqs_client

logger = logging.getLogger(__name__)


def publish_job_message(
    job_id: str,
    user_id: str,
    report_type: str,
    date_range: dict,
    format: str,
    priority: str = "standard",
) -> dict:
    """Publish a job message to the SQS queue.

    Routes to the high-priority queue if priority is "high",
    otherwise to the standard queue.

    Args:
        job_id: Unique job identifier.
        user_id: ID of the user who created the job.
        report_type: Type of report (sales, inventory, analytics).
        date_range: Dict with start_date and end_date.
        format: Output format (csv, pdf, json).
        priority: Message priority ("standard" or "high").

    Returns:
        SQS SendMessage response.

    Raises:
        Exception: If the message fails to publish.
    """
    sqs = get_sqs_client()

    message_body = {
        "job_id": job_id,
        "user_id": user_id,
        "report_type": report_type,
        "date_range": date_range,
        "format": format,
        "priority": priority,
    }

    queue_url = (
        settings.sqs_high_queue_url
        if priority == "high"
        else settings.sqs_standard_queue_url
    )

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
    )

    logger.info(
        "Published job message to SQS",
        extra={"job_id": job_id, "queue_url": queue_url, "priority": priority},
    )

    return response
