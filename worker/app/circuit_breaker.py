"""Circuit Breaker pattern implementation for the worker.

Prevents cascading failures by stopping message consumption when
too many consecutive failures occur.
"""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit Breaker with three states: closed, open, half_open.

    - closed: Normal operation, processing messages
    - open: Too many failures, rejecting messages for recovery_timeout seconds
    - half_open: Testing with one message after recovery timeout
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time: float = 0

    def can_execute(self) -> bool:
        """Check if the circuit allows execution."""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if recovery timeout has elapsed
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = "half_open"
                logger.warning(
                    "Circuit breaker transitioning to half-open",
                    extra={"elapsed_seconds": round(elapsed, 1)},
                )
                return True
            return False

        if self.state == "half_open":
            return True

        return False

    def record_success(self) -> None:
        """Record a successful execution."""
        if self.state == "half_open":
            logger.warning("Circuit breaker closing after successful test")
            self.state = "closed"
        self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "half_open":
            logger.warning("Circuit breaker reopening after failed test")
            self.state = "open"
            return

        if self.failure_count >= self.failure_threshold:
            logger.warning(
                "Circuit breaker opening",
                extra={
                    "failure_count": self.failure_count,
                    "recovery_timeout": self.recovery_timeout,
                },
            )
            self.state = "open"

    async def wait_if_open(self) -> None:
        """If circuit is open, wait until it can transition to half-open."""
        if self.state == "open":
            remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
            if remaining > 0:
                logger.warning(
                    "Circuit breaker is open, waiting",
                    extra={"wait_seconds": round(remaining, 1)},
                )
                await asyncio.sleep(min(remaining, 5))  # Check every 5s max
