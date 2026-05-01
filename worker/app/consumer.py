"""SQS message consumer with concurrent processing.

Polls SQS queues continuously and processes messages in parallel using asyncio.
Integrates Circuit Breaker pattern to prevent cascading failures.
"""

import asyncio
import json
import logging

import boto3

from app.circuit_breaker import CircuitBreaker
from app.config import settings
from app.db.repository import update_job_status
from app.retry import retry_with_backoff

logger = logging.getLogger(__name__)


def _get_sqs_client():
    """Return a boto3 SQS client."""
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("sqs", **kwargs)


async def poll_messages(queue_url: str, sqs_client, max_messages: int = 10) -> list:
    """Poll messages from an SQS queue using long polling.

    Runs the blocking boto3 call in a thread executor to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=settings.worker_poll_interval,
            VisibilityTimeout=settings.worker_visibility_timeout,
        ),
    )
    return response.get("Messages", [])


async def delete_message(queue_url: str, receipt_handle: str, sqs_client, job_id: str = "") -> None:
    """Delete a message from SQS after successful processing."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            lambda: sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
            ),
        )
        logger.info("Deleted message from SQS", extra={"job_id": job_id})
    except Exception as e:
        logger.warning(
            "Failed to delete message from SQS",
            extra={"job_id": job_id, "error": str(e)},
        )


async def process_message(
    message: dict, queue_url: str, sqs_client, processor_fn, circuit_breaker: CircuitBreaker
) -> None:
    """Process a single SQS message with retry and backoff.

    Parses the message body, calls the processor function with exponential backoff retry,
    and deletes the message on success. On failure after exhausting retries, marks the job
    as FAILED and leaves the message in the queue for DLQ routing.
    Records success/failure in the circuit breaker.
    """
    body = json.loads(message["Body"])
    job_id = body.get("job_id", "unknown")
    receipt_handle = message["ReceiptHandle"]

    logger.info("Processing message", extra={"job_id": job_id})

    try:
        await retry_with_backoff(processor_fn, body, job_id=job_id)
        await delete_message(queue_url, receipt_handle, sqs_client, job_id)
        circuit_breaker.record_success()
    except Exception as e:
        logger.error(
            "All retries exhausted for job",
            extra={"job_id": job_id, "error": str(e)},
        )
        # Mark job as FAILED after exhausting retries
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: update_job_status(
                    job_id, "FAILED", error_message=f"Processing failed after retries: {e}"
                ),
            )
        except Exception as db_err:
            logger.error(
                "Failed to update job status to FAILED",
                extra={"job_id": job_id, "error": str(db_err)},
            )
        circuit_breaker.record_failure()
        # Don't delete message — let it go to DLQ after max receives



async def consume_loop(processor_fn, shutdown_event: asyncio.Event | None = None) -> None:
    """Main consumer loop that polls SQS and processes messages concurrently.

    Implements priority-based consumption: always checks the high-priority queue
    first. Only polls the standard queue when the high-priority queue is empty.
    Processes up to `worker_concurrency` messages in parallel.
    Integrates Circuit Breaker to stop consumption after consecutive failures.
    """
    sqs_client = _get_sqs_client()
    high_queue_url = settings.sqs_high_queue_url
    standard_queue_url = settings.sqs_standard_queue_url
    concurrency = settings.worker_concurrency
    circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    logger.info(
        "Starting consumer loop",
        extra={
            "high_queue_url": high_queue_url,
            "standard_queue_url": standard_queue_url,
            "concurrency": concurrency,
        },
    )

    while True:
        if shutdown_event and shutdown_event.is_set():
            logger.info("Shutdown event received, stopping consumer")
            break

        # Circuit breaker check: wait if open
        if not circuit_breaker.can_execute():
            await circuit_breaker.wait_if_open()
            continue

        # Priority: check high-priority queue first
        messages = await poll_messages(high_queue_url, sqs_client, max_messages=concurrency)
        queue_url = high_queue_url

        # If no high-priority messages, check standard queue
        if not messages:
            messages = await poll_messages(standard_queue_url, sqs_client, max_messages=concurrency)
            queue_url = standard_queue_url

        if messages:
            # In half-open state, only process one message as a test
            if circuit_breaker.state == "half_open":
                messages = messages[:1]

            # Process messages concurrently
            tasks = [
                process_message(msg, queue_url, sqs_client, processor_fn, circuit_breaker)
                for msg in messages
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # No messages in either queue, brief pause before next poll
            await asyncio.sleep(0.5)

