"""Unit tests for the Circuit Breaker implementation."""

import asyncio
import time
from unittest.mock import patch

import pytest

from worker.app.circuit_breaker import CircuitBreaker


class TestCircuitBreakerClosed:
    """Tests for the closed (normal) state."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_can_execute_when_closed(self):
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_record_success_resets_failure_count(self):
        cb = CircuitBreaker()
        cb.failure_count = 3
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "closed"

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == "closed"
        assert cb.failure_count == 4


class TestCircuitBreakerOpen:
    """Tests for the open state."""

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(5):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.failure_count == 5

    def test_cannot_execute_when_open(self):
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        for _ in range(5):
            cb.record_failure()
        assert cb.can_execute() is False

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=1)
        for _ in range(5):
            cb.record_failure()
        assert cb.state == "open"

        # Simulate time passing beyond recovery timeout
        cb.last_failure_time = time.time() - 2
        assert cb.can_execute() is True
        assert cb.state == "half_open"


class TestCircuitBreakerHalfOpen:
    """Tests for the half-open state."""

    def test_closes_on_success_in_half_open(self):
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=1)
        # Force into half-open state
        cb.state = "half_open"
        cb.record_success()
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_reopens_on_failure_in_half_open(self):
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=1)
        # Force into half-open state
        cb.state = "half_open"
        cb.record_failure()
        assert cb.state == "open"

    def test_can_execute_when_half_open(self):
        cb = CircuitBreaker()
        cb.state = "half_open"
        assert cb.can_execute() is True


class TestCircuitBreakerWait:
    """Tests for the async wait behavior."""

    @pytest.mark.asyncio
    async def test_wait_if_open_sleeps(self):
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=10)
        for _ in range(5):
            cb.record_failure()

        start = time.time()
        await cb.wait_if_open()
        elapsed = time.time() - start
        # Should sleep for at most 5 seconds (min of remaining, 5)
        assert elapsed < 6

    @pytest.mark.asyncio
    async def test_wait_if_open_does_nothing_when_closed(self):
        cb = CircuitBreaker()
        start = time.time()
        await cb.wait_if_open()
        elapsed = time.time() - start
        assert elapsed < 0.1


class TestCircuitBreakerCustomConfig:
    """Tests for custom configuration."""

    def test_custom_failure_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"

    def test_custom_recovery_timeout(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=30)
        for _ in range(2):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.recovery_timeout == 30
