"""SSE streaming router for real-time job status updates."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.auth.middleware import get_current_user
from app.stream.service import job_status_stream

router = APIRouter(prefix="/stream", tags=["stream"])
logger = logging.getLogger(__name__)


@router.get("/jobs")
async def stream_jobs(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Stream job status updates via Server-Sent Events."""
    user_id = current_user["user_id"]

    async def event_generator():
        async for event in job_status_stream(user_id):
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
