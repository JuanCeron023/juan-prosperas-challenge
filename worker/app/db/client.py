"""DynamoDB client for the worker."""

import boto3
from functools import lru_cache
from app.config import settings


@lru_cache(maxsize=1)
def get_dynamodb_resource():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.resource("dynamodb", **kwargs)


def get_dynamodb_table(table_name: str):
    return get_dynamodb_resource().Table(table_name)
