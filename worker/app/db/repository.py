"""DynamoDB repository for worker state updates."""

from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.db.client import get_dynamodb_table


def _get_jobs_table():
    return get_dynamodb_table(settings.dynamodb_jobs_table)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_job_status(
    job_id: str,
    status: str,
    result_url: str | None = None,
    error_message: str | None = None,
) -> dict:
    """Update a job's status in DynamoDB.

    Args:
        job_id: The job identifier.
        status: New status (PROCESSING, COMPLETED, FAILED).
        result_url: URL of the generated report (for COMPLETED).
        error_message: Error description (for FAILED).

    Returns:
        The updated item attributes.
    """
    table = _get_jobs_table()
    now = _now_iso()

    update_expr_parts = ["#s = :status", "#u = :updated_at"]
    expr_attr_names: dict[str, str] = {"#s": "status", "#u": "updated_at"}
    expr_attr_values: dict[str, Any] = {":status": status, ":updated_at": now}

    if result_url is not None:
        update_expr_parts.append("#r = :result_url")
        expr_attr_names["#r"] = "result_url"
        expr_attr_values[":result_url"] = result_url

    if error_message is not None:
        update_expr_parts.append("#e = :error_message")
        expr_attr_names["#e"] = "error_message"
        expr_attr_values[":error_message"] = error_message

    response = table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET " + ", ".join(update_expr_parts),
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW",
    )
    return response["Attributes"]
