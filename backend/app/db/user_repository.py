"""DynamoDB repository for user CRUD operations.

Provides functions for creating and querying users in the DynamoDB users table.
Uses the GSI `username-index` for efficient lookups by username.
"""

from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from backend.app.config import settings
from backend.app.db.client import get_dynamodb_table


def _get_users_table():
    """Return the users DynamoDB table resource."""
    return get_dynamodb_table(settings.dynamodb_users_table)


def _now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def create_user(user_id: str, username: str, password_hash: str) -> dict:
    """Create a new user in the DynamoDB users table.

    Automatically sets `created_at` to the current timestamp.

    Args:
        user_id: Unique identifier for the user (UUID v4).
        username: The user's unique username.
        password_hash: Bcrypt hash of the user's password.

    Returns:
        The complete user item as stored in DynamoDB.
    """
    table = _get_users_table()
    now = _now_iso()

    item = {
        "user_id": user_id,
        "username": username,
        "password_hash": password_hash,
        "created_at": now,
    }

    table.put_item(Item=item)
    return item


def get_user_by_username(username: str) -> dict | None:
    """Get a user by their username using the GSI.

    Queries the `username-index` GSI to find a user by their unique username.

    Args:
        username: The username to look up.

    Returns:
        The user item as a dictionary, or None if not found.
    """
    table = _get_users_table()

    response = table.query(
        IndexName="username-index",
        KeyConditionExpression=Key("username").eq(username),
        Limit=1,
    )

    items = response.get("Items", [])
    if items:
        return items[0]
    return None
