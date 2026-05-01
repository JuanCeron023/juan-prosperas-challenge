"""SSE service that polls DynamoDB and emits events on job status changes."""

import asyncio
import json
import logging
from typing import AsyncGenerator

from app.db.repository import list_jobs_by_user

logger = logging.getLogger(__name__)

POLL_INTERVAL = 3  # seconds between DynamoDB polls


async def job_status_stream(user_id: str) -> AsyncGenerator[str, None]:
    """Generator that yields SSE events when job statuses change.

    Polls DynamoDB every POLL_INTERVAL seconds and emits events
    for jobs whose status or updated_at has changed.
    """
    # Track last known state of each job
    last_states: dict[str, dict] = {}

    while True:
        try:
            result = list_jobs_by_user(user_id, limit=50)
            jobs = result.get("items", [])

            for job in jobs:
                job_id = job["job_id"]
                current_updated = job.get("updated_at", "")
                last_updated = last_states.get(job_id, {}).get("updated_at", "")

                if current_updated != last_updated:
                    # Status changed — emit event
                    event_data = {
                        "job_id": job_id,
                        "status": job.get("status"),
                        "updated_at": current_updated,
                        "result_url": job.get("result_url"),
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                last_states[job_id] = {
                    "updated_at": current_updated,
                    "status": job.get("status"),
                }

        except Exception as e:
            logger.error("Error polling DynamoDB for SSE", extra={"error": str(e)})

        # Send heartbeat to keep connection alive
        yield ": heartbeat\n\n"

        await asyncio.sleep(POLL_INTERVAL)
