"""
Circuit Breaker — out-of-band stop mechanism for all autonomous actions (Section 9.2).

Enforced at the INFRASTRUCTURE LAYER, independent of the LLM process.
When OPEN, all autonomous tool executions are halted.  Only read-only
queries proceed.  Trip events are logged at CRITICAL severity.

This is the real backstop — it doesn't depend on the model's cooperation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# State enum
# ------------------------------------------------------------------

class CircuitBreakerState(str, Enum):
    CLOSED = "closed"        # Normal operation — all tools allowed
    OPEN = "open"            # Emergency halt — only read-only queries
    HALF_OPEN = "half_open"  # Testing — limited operations, monitoring


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class TripRecord(BaseModel):
    """Metadata about a circuit breaker trip event."""

    reason: str
    operator: str
    tripped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reset_at: datetime | None = None
    reset_by: str | None = None


class CircuitBreakerStatus(BaseModel):
    """Current status of the circuit breaker."""

    state: CircuitBreakerState
    is_operational: bool
    current_trip: TripRecord | None = None
    trip_count: int = 0
    last_changed_at: datetime | None = None


# ------------------------------------------------------------------
# CircuitBreaker
# ------------------------------------------------------------------

class CircuitBreaker:
    """Independent circuit breaker for halting autonomous actions.

    Usage::

        breaker = CircuitBreaker(audit_logger=logger)
        breaker.trip("Suspicious injection pattern detected", "operator-bob")
        # ... investigation ...
        breaker.reset("operator-bob")
    """

    # Tools that are ALWAYS allowed even when the breaker is OPEN
    ALWAYS_ALLOWED: set[str] = {
        "read_file",
        "read_directory",
        "search_code",
    }

    def __init__(self, audit_logger=None) -> None:
        self._state = CircuitBreakerState.CLOSED
        self._current_trip: TripRecord | None = None
        self._trip_count = 0
        self._last_changed: datetime | None = None
        self.audit_logger = audit_logger

    # ------------------------------------------------------------------
    # State control
    # ------------------------------------------------------------------

    def trip(self, reason: str, operator: str) -> CircuitBreakerStatus:
        """OPEN the breaker — halt all autonomous actions.

        Args:
            reason: Why the breaker was tripped.
            operator: Who tripped it (for audit trail).
        """
        self._state = CircuitBreakerState.OPEN
        self._current_trip = TripRecord(reason=reason, operator=operator)
        self._trip_count += 1
        self._last_changed = datetime.now(timezone.utc)
        self._audit_critical(
            f"CIRCUIT BREAKER TRIPPED by {operator}: {reason}"
        )
        return self.status()

    def reset(self, operator: str) -> CircuitBreakerStatus:
        """CLOSE the breaker — resume normal operation.

        Args:
            operator: Who reset it (for audit trail).
        """
        if self._current_trip:
            self._current_trip.reset_at = datetime.now(timezone.utc)
            self._current_trip.reset_by = operator

        self._state = CircuitBreakerState.CLOSED
        self._last_changed = datetime.now(timezone.utc)
        self._audit_critical(
            f"CIRCUIT BREAKER RESET by {operator}"
        )
        return self.status()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def is_operational(self) -> bool:
        """Can autonomous actions proceed?

        Returns False when the breaker is OPEN.
        """
        return self._state != CircuitBreakerState.OPEN

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a specific tool is allowed given the current state.

        When the breaker is OPEN, only ALWAYS_ALLOWED tools pass.
        When CLOSED, all tools pass.
        """
        if self._state == CircuitBreakerState.OPEN:
            return tool_name in self.ALWAYS_ALLOWED
        return True

    def status(self) -> CircuitBreakerStatus:
        """Return the current circuit breaker status."""
        return CircuitBreakerStatus(
            state=self._state,
            is_operational=self.is_operational(),
            current_trip=self._current_trip,
            trip_count=self._trip_count,
            last_changed_at=self._last_changed,
        )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def _audit_critical(self, message: str) -> None:
        """Log a CRITICAL-severity event to the audit log."""
        if not self.audit_logger:
            return
        from trust_safety.governance.audit_log.models import AuditEntry
        entry = AuditEntry(
            event_type="circuit_breaker",
            action=message,
            risk_score=1.0,
            status="blocked" if self._state == CircuitBreakerState.OPEN else "allowed",
            metadata={
                "state": self._state.value,
                "trip_count": self._trip_count,
                "trip_reason": self._current_trip.reason if self._current_trip else None,
            },
        )
        self.audit_logger.log(entry)
