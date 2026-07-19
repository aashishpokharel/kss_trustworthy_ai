"""
HITL Approval Queue — human-in-the-loop gate for high-risk tool calls (Section 9.2).

Key safety property: **FAIL CLOSED**.  If no human responds before the
timeout, the action is DENIED.  Never auto-approve on timeout.

The queue is in-memory for local dev.  A future production phase can add
persistent storage (Redis, Postgres) while keeping the same API surface.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from trust_safety.orchestrator.tool_registry import RiskTier


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMED_OUT = "timed_out"


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class ApprovalRequest(BaseModel):
    """A request for human approval before executing a tool call."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    tool_params: dict[str, Any] = Field(default_factory=dict)
    risk_tier: RiskTier
    requester: str = "system"
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer: str | None = None
    denial_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_seconds: int = Field(default=300, ge=30, le=86400)
    resolved_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if this request has exceeded its timeout."""
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return elapsed > self.timeout_seconds


# ------------------------------------------------------------------
# ApprovalQueue
# ------------------------------------------------------------------

class ApprovalQueue:
    """In-memory queue for human-in-the-loop approval requests.

    Usage::

        queue = ApprovalQueue(timeout_seconds=300)
        req = queue.submit("delete_file", {"path": "/tmp/x"}, RiskTier.HIGH)
        # ... human reviews ...
        queue.approve(req.request_id, "operator-alice")
    """

    def __init__(self, timeout_seconds: int = 300, audit_logger=None) -> None:
        self._pending: dict[str, ApprovalRequest] = {}
        self._history: list[ApprovalRequest] = []
        self.timeout_seconds = timeout_seconds
        self.audit_logger = audit_logger

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def submit(
        self,
        tool_name: str,
        tool_params: dict[str, Any],
        risk_tier: RiskTier,
        requester: str = "system",
        reason: str = "",
    ) -> ApprovalRequest:
        """Submit a tool call for human approval.

        Returns the pending ApprovalRequest.
        """
        # Check for expired requests and auto-deny them first
        self.check_timeouts()

        request = ApprovalRequest(
            tool_name=tool_name,
            tool_params=tool_params,
            risk_tier=risk_tier,
            requester=requester,
            reason=reason,
            timeout_seconds=self.timeout_seconds,
        )
        self._pending[request.request_id] = request
        self._audit("hitl_submitted", request)
        return request

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def approve(self, request_id: str, reviewer: str) -> ApprovalRequest:
        """Approve a pending request."""
        request = self._get_pending(request_id)
        request.status = ApprovalStatus.APPROVED
        request.reviewer = reviewer
        request.resolved_at = datetime.now(timezone.utc)
        self._move_to_history(request)
        self._audit("hitl_approved", request)
        return request

    def deny(self, request_id: str, reviewer: str, reason: str = "") -> ApprovalRequest:
        """Deny a pending request."""
        request = self._get_pending(request_id)
        request.status = ApprovalStatus.DENIED
        request.reviewer = reviewer
        request.denial_reason = reason
        request.resolved_at = datetime.now(timezone.utc)
        self._move_to_history(request)
        self._audit("hitl_denied", request)
        return request

    # ------------------------------------------------------------------
    # Timeout handling (FAIL CLOSED)
    # ------------------------------------------------------------------

    def check_timeouts(self) -> list[ApprovalRequest]:
        """Auto-deny all expired requests.  FAIL CLOSED.

        Returns the list of timed-out requests.
        """
        timed_out: list[ApprovalRequest] = []
        for req_id in list(self._pending.keys()):
            request = self._pending[req_id]
            if request.is_expired():
                request.status = ApprovalStatus.TIMED_OUT
                request.resolved_at = datetime.now(timezone.utc)
                self._move_to_history(request)
                timed_out.append(request)
                self._audit("hitl_timed_out", request)
        return timed_out

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_pending(self) -> list[ApprovalRequest]:
        """List all pending (unresolved) approval requests."""
        self.check_timeouts()
        return list(self._pending.values())

    def get_history(self, limit: int = 50) -> list[ApprovalRequest]:
        """List resolved requests, most recent first."""
        return sorted(
            self._history,
            key=lambda r: r.resolved_at or r.created_at,
            reverse=True,
        )[:limit]

    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Look up any request by ID (pending or historical)."""
        if request_id in self._pending:
            return self._pending[request_id]
        for r in self._history:
            if r.request_id == request_id:
                return r
        return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, int]:
        """Return counts by status."""
        self.check_timeouts()
        counts = {"pending": 0, "approved": 0, "denied": 0, "timed_out": 0}
        counts["pending"] = len(self._pending)
        for r in self._history:
            key = r.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_pending(self, request_id: str) -> ApprovalRequest:
        """Get a pending request or raise ValueError."""
        if request_id not in self._pending:
            raise ValueError(f"Approval request '{request_id}' not found or already resolved.")
        return self._pending[request_id]

    def _move_to_history(self, request: ApprovalRequest) -> None:
        """Move a resolved request from pending to history."""
        self._pending.pop(request.request_id, None)
        self._history.append(request)

    def _audit(self, event: str, request: ApprovalRequest) -> None:
        """Log to audit log if available."""
        if not self.audit_logger:
            return
        from trust_safety.governance.audit_log.models import AuditEntry
        entry = AuditEntry(
            event_type=event,
            action=f"HITL {event} for {request.tool_name}",
            risk_tier=request.risk_tier,
            user_id=request.reviewer or request.requester,
            status=request.status.value,
            metadata={
                "request_id": request.request_id,
                "tool_name": request.tool_name,
                "risk_tier": request.risk_tier.value,
                "denial_reason": request.denial_reason,
            },
        )
        self.audit_logger.log(entry)
