"""Job status enum for the report processing system."""

from enum import Enum


class JobStatus(str, Enum):
    """Possible states of a report generation job."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
