"""Tests for retry logic and availability circuit breaker."""

import asyncio

import pytest

from trust_safety.llm.retry import AvailabilityBreaker, BreakerState, with_retry


class TestRetry:
    """Exponential backoff with jitter."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await with_retry(succeed, max_retries=3)
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self):
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timed out")
            return "finally"

        result = await with_retry(flaky, max_retries=3, backoff_base=0.01)
        assert result == "finally"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self):
        async def always_fails():
            raise TimeoutError("always")

        with pytest.raises(TimeoutError):
            await with_retry(always_fails, max_retries=2, backoff_base=0.01)

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        call_count = 0

        async def auth_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Auth failed: 401 Unauthorized")

        with pytest.raises(RuntimeError, match="Auth"):
            await with_retry(auth_fail, max_retries=3, backoff_base=0.01)
        assert call_count == 1  # No retry on auth failure


class TestAvailabilityBreaker:
    """Availability circuit breaker (separate from safety breaker)."""

    def test_initial_state_closed(self):
        breaker = AvailabilityBreaker()
        assert breaker.state == BreakerState.CLOSED
        assert breaker.allow_request()

    def test_trips_after_threshold(self):
        breaker = AvailabilityBreaker(failure_threshold=3)
        breaker.failure()
        breaker.failure()
        assert breaker.allow_request()  # Still closed
        breaker.failure()
        assert breaker.state == BreakerState.OPEN
        assert not breaker.allow_request()

    def test_success_resets(self):
        breaker = AvailabilityBreaker(failure_threshold=3)
        breaker.failure()
        breaker.failure()
        breaker.success()
        assert breaker.state == BreakerState.CLOSED
        assert breaker.failure_count == 0

    def test_half_open_allows_probe(self):
        breaker = AvailabilityBreaker(
            failure_threshold=1,
            reset_timeout_seconds=-1,  # Already expired
        )
        breaker.failure()
        assert breaker.state == BreakerState.OPEN
        # Timeout has passed → should transition to HALF_OPEN and allow
        assert breaker.allow_request()
        assert breaker.state == BreakerState.HALF_OPEN
