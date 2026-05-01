"""Dependency injection for FastAPI.

Provides shared clients for DynamoDB and SQS that can be overridden in tests.
"""

from app.db.client import get_dynamodb_resource
from app.queue.client import get_sqs_client


def get_db():
    """Return the DynamoDB resource."""
    return get_dynamodb_resource()


def get_queue():
    """Return the SQS client."""
    return get_sqs_client()
