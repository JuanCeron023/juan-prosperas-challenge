"""Jobs router with REST endpoints for report management."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from backend.app.auth.middleware import get_current_user
from backend.app.jobs.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobListResponse,
    JobResponse,
)
from backend.app.jobs.service import create_job, get_job, list_user_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=JobCreateResponse)
async def create_report_job(
    request: JobCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> JobCreateResponse:
    """Create a new report job."""
    result = create_job(
        user_id=current_user["user_id"],
        report_type=request.report_type,
        date_range={
            "start_date": request.date_range.start_date.isoformat(),
            "end_date": request.date_range.end_date.isoformat(),
        },
        format=request.format,
        priority=request.priority,
    )
    return JobCreateResponse(**result)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
) -> JobListResponse:
    """List all jobs for the authenticated user (paginated)."""
    result = list_user_jobs(
        user_id=current_user["user_id"],
        page=page,
        limit=limit,
        cursor=cursor,
    )
    return JobListResponse(**result)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> JobResponse:
    """Get the status and details of a specific job."""
    job = get_job(job_id=job_id, user_id=current_user["user_id"])
    return JobResponse(**job)
