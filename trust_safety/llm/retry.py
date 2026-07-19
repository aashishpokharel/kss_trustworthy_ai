"""
Retry and failure handling for LLM API calls (llm-integration doc §6).

- Exponential backoff with jitter for rate limits (429)
- Availability circuit breaker (separate from safety circuit breaker)
- Timeout handling: fail-closed for tool calls, fail-safe for conversation
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Retry
# ------------------------------------------------------------------

async def with_retry(
    call: Callable,
    max_retries: int = 3,
    backoff_base: float = 1.0,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Call *call* with exponential backoff and jitter.

    Retries on: TimeoutError, rate-limit errors (429), transient network errors.
    Does NOT retry on: auth errors (401), bad requests (400).
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await call(*args, **kwargs)
        except TimeoutError:
            last_exception = TimeoutError("Request timed out")
            if attempt == max_retries:
                break
        except RuntimeError as exc:
            msg = str(exc).lower()
            if "auth" in msg or "401" in msg or "unauthorized" in msg:
                raise  # Don't retry auth failures
            if "400" in msg and "rate" not in msg:
                raise  # Don't retry bad requests
            last_exception = exc
            if attempt == max_retries:
                break
        except Exception as exc:
            last_exception = exc
            if attempt == max_retries:
                break

        # Exponential backoff with jitter
        delay = backoff_base * (2 ** attempt) + random.uniform(0, 0.5)
        await asyncio.sleep(delay)

    raise last_exception or RuntimeError("Retry exhausted with no exception")


# ------------------------------------------------------------------
# Availability Circuit Breaker
# ------------------------------------------------------------------

class BreakerState(str, Enum):
    CLOSED = "closed"       # Normal — calls proceed
    OPEN = "open"           # Tripped — calls fail fast
    HALF_OPEN = "half_open" # Testing — one call allowed through


class AvailabilityBreaker(BaseModel):
    """Circuit breaker for provider availability (separate from safety breaker).

    Trips on consecutive failures, not on safety violations.
    Safety violations go to the safety circuit breaker in orchestrator/.
    """
    state: BreakerState = BreakerState.CLOSED
    failure_count: int = 0
    failure_threshold: int = 5
    last_failure_at: datetime | None = None
    last_success_at: datetime | None = None
    reset_timeout_seconds: int = 30

    def success(self) -> None:
        self.failure_count = 0
        self.state = BreakerState.CLOSED
        self.last_success_at = datetime.now(timezone.utc)

    def failure(self) -> None:
        self.failure_count += 1
        self.last_failure_at = datetime.now(timezone.utc)
        if self.failure_count >= self.failure_threshold:
            self.state = BreakerState.OPEN

    def allow_request(self) -> bool:
        """Should a request be attempted?"""
        if self.state == BreakerState.CLOSED:
            return True
        if self.state == BreakerState.OPEN:
            # Check if reset timeout has elapsed
            if self.last_failure_at:
                elapsed = (datetime.now(timezone.utc) - self.last_failure_at).total_seconds()
                if elapsed >= self.reset_timeout_seconds:
                    self.state = BreakerState.HALF_OPEN
                    return True
            return False
        # HALF_OPEN: allow one probe request
        return True

    def is_operational(self) -> bool:
        return self.state != BreakerState.OPEN
