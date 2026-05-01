"""DynamoDB client initialization.

Provides a configurable boto3 DynamoDB resource that works with both
LocalStack (local development) and real AWS (production).
"""

import boto3
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_dynamodb_resource():
    """Return a boto3 DynamoDB resource.

    If `aws_endpoint_url` is set (LocalStack), the resource connects to that
    endpoint. Otherwise, it uses the default AWS configuration.

    Returns:
        boto3 DynamoDB ServiceResource
    """
    kwargs = {
        "region_name": settings.aws_region,
    }
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url

    return boto3.resource("dynamodb", **kwargs)


def get_dynamodb_table(table_name: str):
    """Return a DynamoDB Table resource for the given table name.

    Args:
        table_name: Name of the DynamoDB table.

    Returns:
        boto3 DynamoDB Table resource
    """
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(table_name)
