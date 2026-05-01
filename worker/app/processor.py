"""Simulated report processor.

Simulates report generation with a random sleep and dummy data.
Updates job status in DynamoDB through the processing lifecycle.
"""

import asyncio
import logging
import random
import uuid

from worker.app.db.repository import update_job_status

logger = logging.getLogger(__name__)

# Simulate a 10% failure rate for testing resilience
FAILURE_RATE = 0.1


async def process_report(message: dict) -> None:
    """Process a report generation job.

    Updates status to PROCESSING, simulates work with a random sleep,
    then updates to COMPLETED or FAILED.

    Args:
        message: Parsed SQS message containing job_id, report_type, format, etc.

    Raises:
        Exception: If the simulated processing fails.
    """
    job_id = message["job_id"]
    report_type = message.get("report_type", "unknown")
    output_format = message.get("format", "csv")

    logger.info("Starting report processing", extra={"job_id": job_id, "report_type": report_type})

    # Update status to PROCESSING
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: update_job_status(job_id, "PROCESSING"))

    # Simulate processing time (5-30 seconds)
    processing_time = random.uniform(5, 30)
    logger.info(
        "Simulating processing",
        extra={"job_id": job_id, "duration_seconds": round(processing_time, 1)},
    )
    await asyncio.sleep(processing_time)

    # Simulate occasional failures
    if random.random() < FAILURE_RATE:
        error_msg = f"Simulated failure during {report_type} report generation"
        logger.error("Report processing failed", extra={"job_id": job_id, "error": error_msg})
        await loop.run_in_executor(
            None,
            lambda: update_job_status(job_id, "FAILED", error_message=error_msg),
        )
        raise Exception(error_msg)

    # Generate dummy result URL
    result_url = f"https://reports.example.com/{job_id}/report.{output_format}"

    # Update status to COMPLETED
    await loop.run_in_executor(
        None,
        lambda: update_job_status(job_id, "COMPLETED", result_url=result_url),
    )

    logger.info("Report processing completed", extra={"job_id": job_id, "result_url": result_url})
