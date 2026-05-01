"""SQS client initialization.

Provides a configurable boto3 SQS client that works with both
LocalStack (local development) and real AWS (production).
"""

import boto3
from functools import lru_cache

from backend.app.config import settings


@lru_cache(maxsize=1)
def get_sqs_client():
    """Return a boto3 SQS client.

    If `aws_endpoint_url` is set (LocalStack), connects to that endpoint.
    Otherwise uses default AWS configuration.

    Returns:
        boto3 SQS client
    """
    kwargs = {
        "region_name": settings.aws_region,
    }
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url

    return boto3.client("sqs", **kwargs)
