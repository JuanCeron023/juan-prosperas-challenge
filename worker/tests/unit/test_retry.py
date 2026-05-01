"""Unit tests for the retry with exponential backoff implementation."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.retry import retry_with_backoff


class TestRetryWithBackoffSuccess:
    """Tests for successful execution scenarios."""

    @pytest.mark.asyncio
    async def test_returns_result_on_first_try(self):
        func = AsyncMock(return_value="success")
        result = await retry_with_backoff(func, "arg1", job_id="job-1")
        assert result == "success"
        assert func.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_result_after_retries(self):
        func = AsyncMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        with patch("app.retry.asyncio.sleep", new_callable=AsyncMock):
            result = await retry_with_backoff(func, "arg1", job_id="job-1")
        assert result == "success"
        assert func.call_count == 3

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs_to_func(self):
        func = AsyncMock(return_value="ok")
        await retry_with_backoff(func, "a", "b", job_id="job-1", key="value")
        func.assert_called_once_with("a", "b", key="value")


class TestRetryWithBackoffFailure:
    """Tests for failure scenarios."""

    @pytest.mark.asyncio
    async def test_raises_last_exception_after_max_retries(self):
        func = AsyncMock(side_effect=ValueError("persistent error"))
        with patch("app.retry.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ValueError, match="persistent error"):
                await retry_with_backoff(func, job_id="job-1")
        assert func.call_count == 3

    @pytest.mark.asyncio
    async def test_custom_max_retries(self):
        func = AsyncMock(side_effect=RuntimeError("fail"))
        with patch("app.retry.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError):
                await retry_with_backoff(func, max_retries=5, job_id="job-1")
        assert func.call_count == 5


class TestRetryWithBackoffDelays:
    """Tests for exponential backoff delay calculation."""

    @pytest.mark.asyncio
    async def test_exponential_delays_with_jitter(self):
        func = AsyncMock(side_effect=[Exception("e1"), Exception("e2"), "ok"])
        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("app.retry.asyncio.sleep", side_effect=mock_sleep):
            with patch("app.retry.random.uniform", return_value=0.0):
                await retry_with_backoff(func, job_id="job-1")

        # With 0 jitter: delays should be exactly 1s, 2s
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 1.0  # base_delay * 2^0
        assert sleep_calls[1] == 2.0  # base_delay * 2^1

    @pytest.mark.asyncio
    async def test_delay_within_jitter_bounds(self):
        func = AsyncMock(side_effect=[Exception("e1"), "ok"])
        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("app.retry.asyncio.sleep", side_effect=mock_sleep):
            await retry_with_backoff(func, job_id="job-1", base_delay=1.0, jitter_ms=500)

        # Delay should be 1.0 ± 0.5 → [0.5, 1.5]
        assert len(sleep_calls) == 1
        assert 0.0 <= sleep_calls[0] <= 1.5

    @pytest.mark.asyncio
    async def test_no_sleep_after_last_attempt(self):
        func = AsyncMock(side_effect=Exception("always fails"))
        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("app.retry.asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(Exception):
                await retry_with_backoff(func, max_retries=3, job_id="job-1")

        # Should only sleep between attempts, not after the last one
        assert len(sleep_calls) == 2


class TestRetryWithBackoffLogging:
    """Tests for logging behavior."""

    @pytest.mark.asyncio
    async def test_logs_each_retry_attempt(self):
        func = AsyncMock(side_effect=[Exception("e1"), Exception("e2"), "ok"])

        with patch("app.retry.asyncio.sleep", new_callable=AsyncMock):
            with patch("app.retry.logger") as mock_logger:
                await retry_with_backoff(func, job_id="test-job")

        # Should log 2 retry attempts (attempt 1 and 2, then success on 3)
        assert mock_logger.info.call_count == 2
        # Verify first call includes attempt info
        first_call_args = mock_logger.info.call_args_list[0]
        assert "1/3" in first_call_args[0][0] % first_call_args[0][1:]
