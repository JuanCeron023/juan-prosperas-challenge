"""SSE streaming router for real-time job status updates."""

import logging

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse

from app.auth.service import decode_token
from app.stream.service import job_status_stream

router = APIRouter(prefix="/stream", tags=["stream"])
logger = logging.getLogger(__name__)


async def get_current_user_from_token(token: str) -> dict:
    """Extract user info from JWT token (supports both header and query param)."""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        username = payload.get("username")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID",
            )
        return {"user_id": user_id, "username": username}
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
        )


@router.get("/jobs")
async def stream_jobs(
    request: Request,
    token: str = Query(...),  # Token from query param (EventSource limitation)
):
    """Stream job status updates via Server-Sent Events.

    Note: EventSource doesn't support custom headers, so token must be
    passed as query parameter: /stream/jobs?token=<jwt>
    """
    # Validate token and get user
    current_user = await get_current_user_from_token(token)
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
