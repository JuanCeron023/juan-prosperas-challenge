"""Application configuration using Pydantic Settings.

Supports both LocalStack (local development) and real AWS (production)
via environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None  # Set for LocalStack, None for real AWS

    # JWT Configuration
    jwt_secret: str = "change-me-in-production"
    jwt_expiration_minutes: int = 60

    # DynamoDB Tables
    dynamodb_jobs_table: str = "jobs"
    dynamodb_users_table: str = "users"

    # SQS Queues
    sqs_standard_queue_url: str = "http://localhost:4566/000000000000/reports-queue-standard"
    sqs_high_queue_url: str = "http://localhost:4566/000000000000/reports-queue-high"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
