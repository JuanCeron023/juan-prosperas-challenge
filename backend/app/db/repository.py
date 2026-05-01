"""DynamoDB repository for job CRUD operations.

Provides functions for creating, reading, updating, and listing jobs
in the DynamoDB jobs table. Uses the GSI `user-jobs-index` for efficient
queries by user_id with cursor-based pagination.
"""

from datetime import datetime, timezone
from typing import Any

from boto3.dynamodb.conditions import Key

from backend.app.config import settings
from backend.app.db.client import get_dynamodb_table


def _get_jobs_table():
    """Return the jobs DynamoDB table resource."""
    return get_dynamodb_table(settings.dynamodb_jobs_table)


def _now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def create_job(job_data: dict) -> dict:
    """Create a new job in the DynamoDB jobs table.

    Automatically sets `created_at` and `updated_at` to the current timestamp.

    Args:
        job_data: Dictionary with job attributes. Must include at minimum:
            job_id, user_id, status, report_type, format, priority, date_range.

    Returns:
        The complete job item as stored in DynamoDB.
    """
    table = _get_jobs_table()
    now = _now_iso()

    item = {
        **job_data,
        "created_at": now,
        "updated_at": now,
    }

    # Remove None values to avoid storing empty attributes
    item = {k: v for k, v in item.items() if v is not None}

    table.put_item(Item=item)
    return item


def get_job(job_id: str) -> dict | None:
    """Get a job by its job_id.

    Args:
        job_id: The unique identifier of the job.

    Returns:
        The job item as a dictionary, or None if not found.
    """
    table = _get_jobs_table()
    response = table.get_item(Key={"job_id": job_id})
    return response.get("Item")


def update_job_status(
    job_id: str,
    status: str,
    result_url: str | None = None,
    error_message: str | None = None,
) -> dict:
    """Update the status of a job and automatically set updated_at.

    Args:
        job_id: The unique identifier of the job.
        status: The new status value (e.g., PROCESSING, COMPLETED, FAILED).
        result_url: Optional URL of the generated report (set on COMPLETED).
        error_message: Optional error message (set on FAILED).

    Returns:
        The updated job item attributes.
    """
    table = _get_jobs_table()
    now = _now_iso()

    update_expr_parts = ["#s = :status", "#u = :updated_at"]
    expr_attr_names: dict[str, str] = {
        "#s": "status",
        "#u": "updated_at",
    }
    expr_attr_values: dict[str, Any] = {
        ":status": status,
        ":updated_at": now,
    }

    if result_url is not None:
        update_expr_parts.append("#r = :result_url")
        expr_attr_names["#r"] = "result_url"
        expr_attr_values[":result_url"] = result_url

    if error_message is not None:
        update_expr_parts.append("#e = :error_message")
        expr_attr_names["#e"] = "error_message"
        expr_attr_values[":error_message"] = error_message

    update_expression = "SET " + ", ".join(update_expr_parts)

    response = table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW",
    )
    return response["Attributes"]


def list_jobs_by_user(
    user_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> dict:
    """List jobs for a user with cursor-based pagination using the GSI.

    Queries the `user-jobs-index` GSI with user_id as partition key,
    ordered by created_at (sort key) in descending order (newest first).

    Args:
        user_id: The user ID to query jobs for.
        limit: Maximum number of items to return per page (default 20).
        cursor: Opaque pagination cursor (the created_at value of the last
            item from the previous page). None for the first page.

    Returns:
        Dictionary with keys:
            - items: List of job items for the current page.
            - total: Total count of jobs for this user.
            - next_cursor: Cursor for the next page, or None if no more pages.
    """
    table = _get_jobs_table()

    # Build query parameters
    query_kwargs: dict[str, Any] = {
        "IndexName": "user-jobs-index",
        "KeyConditionExpression": Key("user_id").eq(user_id),
        "ScanIndexForward": False,  # Descending order (newest first)
        "Limit": limit,
    }

    if cursor:
        # Use ExclusiveStartKey for pagination
        query_kwargs["ExclusiveStartKey"] = {
            "user_id": user_id,
            "created_at": cursor,
            "job_id": _get_job_id_for_cursor(table, user_id, cursor),
        }

    response = table.query(**query_kwargs)
    items = response.get("Items", [])

    # Determine next_cursor from LastEvaluatedKey
    next_cursor = None
    last_evaluated_key = response.get("LastEvaluatedKey")
    if last_evaluated_key:
        next_cursor = last_evaluated_key.get("created_at")

    # Get total count for this user (separate query with Select=COUNT)
    count_response = table.query(
        IndexName="user-jobs-index",
        KeyConditionExpression=Key("user_id").eq(user_id),
        Select="COUNT",
    )
    total = count_response.get("Count", 0)

    return {
        "items": items,
        "total": total,
        "next_cursor": next_cursor,
    }


def _get_job_id_for_cursor(table, user_id: str, created_at: str) -> str:
    """Retrieve the job_id for a given user_id and created_at to build ExclusiveStartKey.

    DynamoDB requires the full primary key of the table (job_id) plus the GSI keys
    in ExclusiveStartKey. This helper fetches the job_id for the cursor position.

    Args:
        table: The DynamoDB table resource.
        user_id: The user ID.
        created_at: The created_at timestamp used as cursor.

    Returns:
        The job_id corresponding to the cursor position.
    """
    response = table.query(
        IndexName="user-jobs-index",
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("created_at").eq(created_at),
        Limit=1,
    )
    items = response.get("Items", [])
    if items:
        return items[0]["job_id"]
    # Fallback: return empty string (query will start from beginning)
    return ""
