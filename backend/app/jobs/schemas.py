"""Pydantic schemas for job endpoints."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, model_validator

from app.jobs.enums import JobStatus


class DateRange(BaseModel):
    """Date range for report generation."""

    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        return self


class JobCreateRequest(BaseModel):
    """Request body for POST /jobs."""

    report_type: Literal["sales", "inventory", "analytics"]
    date_range: DateRange
    format: Literal["csv", "pdf", "json"]
    priority: Literal["standard", "high"] = "standard"


class JobCreateResponse(BaseModel):
    """Response body for POST /jobs."""

    job_id: str
    status: Literal["PENDING"] = "PENDING"


class JobResponse(BaseModel):
    """Response body for GET /jobs/{job_id}."""

    job_id: str
    user_id: str
    status: JobStatus
    report_type: str
    created_at: str
    updated_at: str
    result_url: Optional[str] = None
    error_message: Optional[str] = None


class JobListResponse(BaseModel):
    """Response body for GET /jobs."""

    items: list[JobResponse]
    total: int
    page: int
    next_cursor: Optional[str] = None
