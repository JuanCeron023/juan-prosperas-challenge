"""Retry with exponential backoff and jitter.

Implements retry logic with exponential delays (1s, 2s, 4s) and
random jitter (±500ms) to avoid thundering herd.
"""

import asyncio
import logging
import random
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    func: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    jitter_ms: int = 500,
    job_id: str = "",
    **kwargs: Any,
) -> Any:
    """Execute an async function with exponential backoff retry.

    Delays: base_delay * 2^attempt ± jitter_ms
    - Attempt 0: 1s ± 500ms → [0.5s, 1.5s]
    - Attempt 1: 2s ± 500ms → [1.5s, 2.5s]
    - Attempt 2: 4s ± 500ms → [3.5s, 4.5s]

    Args:
        func: Async function to execute.
        *args: Positional arguments for func.
        max_retries: Maximum number of retry attempts (default 3).
        base_delay: Base delay in seconds (default 1.0).
        jitter_ms: Jitter range in milliseconds (default 500).
        job_id: Job ID for logging context.
        **kwargs: Keyword arguments for func.

    Returns:
        The result of the function call.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(-jitter_ms / 1000, jitter_ms / 1000)
            actual_delay = max(0, delay + jitter)

            logger.info(
                "Retry attempt %d/%d for job %s, waiting %.2fs",
                attempt + 1,
                max_retries,
                job_id,
                actual_delay,
                extra={
                    "job_id": job_id,
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "delay_seconds": round(actual_delay, 2),
                    "error": str(e),
                },
            )

            if attempt < max_retries - 1:
                await asyncio.sleep(actual_delay)

    raise last_exception  # type: ignore[misc]
