"""Business logic for job management."""

import logging
import uuid

from fastapi import HTTPException, status

from backend.app.db.repository import (
    create_job as db_create_job,
    get_job as db_get_job,
    list_jobs_by_user as db_list_jobs_by_user,
    update_job_status,
)
from backend.app.jobs.enums import JobStatus
from backend.app.queue.publisher import publish_job_message

logger = logging.getLogger(__name__)


def create_job(
    user_id: str,
    report_type: str,
    date_range: dict,
    format: str,
    priority: str = "standard",
) -> dict:
    """Create a new report job.

    Creates the job in DynamoDB with PENDING status, then publishes
    a message to SQS. If SQS publish fails, marks the job as FAILED.

    Args:
        user_id: ID of the authenticated user creating the job.
        report_type: Type of report (sales, inventory, analytics).
        date_range: Dict with start_date and end_date.
        format: Output format (csv, pdf, json).
        priority: Job priority ("standard" or "high").

    Returns:
        Dict with job_id and status "PENDING".

    Raises:
        HTTPException: 503 if SQS publish fails.
    """
    job_id = str(uuid.uuid4())

    # Create job in DynamoDB
    db_create_job({
        "job_id": job_id,
        "user_id": user_id,
        "status": JobStatus.PENDING.value,
        "report_type": report_type,
        "format": format,
        "priority": priority,
        "date_range": date_range,
    })

    # Publish to SQS
    try:
        publish_job_message(
            job_id=job_id,
            user_id=user_id,
            report_type=report_type,
            date_range=date_range,
            format=format,
            priority=priority,
        )
    except Exception as e:
        logger.error(
            "Failed to publish job to SQS",
            extra={"job_id": job_id, "error": str(e)},
        )
        update_job_status(
            job_id, JobStatus.FAILED.value, error_message="Failed to enqueue job"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enqueue job for processing",
        )

    return {"job_id": job_id, "status": JobStatus.PENDING.value}


def get_job(job_id: str, user_id: str) -> dict:
    """Get a job by ID, verifying ownership.

    Args:
        job_id: The unique identifier of the job.
        user_id: The ID of the requesting user (for ownership check).

    Returns:
        The job item as a dictionary.

    Raises:
        HTTPException: 404 if not found, 403 if belongs to another user.
    """
    job = db_get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    return job


def list_user_jobs(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    cursor: str | None = None,
) -> dict:
    """List jobs for a user with pagination.

    Args:
        user_id: The user ID to list jobs for.
        page: Current page number (for response metadata).
        limit: Maximum number of items per page.
        cursor: Opaque pagination cursor for the next page.

    Returns:
        Dict with items, total, page, and next_cursor.
    """
    result = db_list_jobs_by_user(user_id, limit=limit, cursor=cursor)
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "next_cursor": result["next_cursor"],
    }
