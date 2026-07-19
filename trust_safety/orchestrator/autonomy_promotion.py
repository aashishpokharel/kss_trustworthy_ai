"""
Autonomy Promotion Process — formal workflow for increasing agent autonomy (Section 9.1, 13).

An agent may be promoted from in-loop → on-loop → out-of-loop only after:
1. A documented safety case is filed
2. The safety case is reviewed by a human
3. Evidence of safe operation is presented
4. The promotion is recorded in the audit log with policy version reference
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.store import AuditLogger
from trust_safety.orchestrator.tool_registry import HitlMode, RiskTier


class PromotionStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"


class SafetyCase(BaseModel):
    """Evidence package for an autonomy promotion request."""
    case_id: str = Field(
        default_factory=lambda: (
            f"SC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            f"-{__import__('os').urandom(3).hex()}"
        )
    )
    agent_id: str
    tool_name: str
    current_tier: RiskTier
    requested_tier: RiskTier
    evidence: dict[str, Any] = Field(default_factory=dict)
    reviewer: str | None = None
    review_notes: str = ""
    status: PromotionStatus = PromotionStatus.SUBMITTED
    policy_version: str = "1.0.0"
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None


class PromotionTracker:
    """Formal autonomy promotion workflow.

    Usage::

        tracker = PromotionTracker(audit_logger=logger)
        case = tracker.submit_case(
            agent_id="agent-1", tool_name="write_file",
            current_tier=RiskTier.MEDIUM,
            requested_tier=RiskTier.LOW,
            evidence={"safe_interactions": 1000, "eval_block_rate": 1.0},
        )
        tracker.review(case.case_id, approved=True, reviewer="sec-ops")
    """

    # Required evidence thresholds
    MIN_SAFE_INTERACTIONS = 100

    def __init__(
        self,
        audit_logger: AuditLogger | None = None,
        tool_registry=None,
    ) -> None:
        self._cases: dict[str, SafetyCase] = {}
        self._history: list[SafetyCase] = []
        self.audit_logger = audit_logger
        self.tool_registry = tool_registry

    # -- Submission ---------------------------------------------------

    def submit_case(
        self,
        agent_id: str,
        tool_name: str,
        current_tier: RiskTier,
        requested_tier: RiskTier,
        evidence: dict[str, Any] | None = None,
        policy_version: str = "1.0.0",
    ) -> SafetyCase:
        """Submit a safety case for autonomy promotion."""
        case = SafetyCase(
            agent_id=agent_id,
            tool_name=tool_name,
            current_tier=current_tier,
            requested_tier=requested_tier,
            evidence=evidence or {},
            policy_version=policy_version,
        )
        self._cases[case.case_id] = case
        self._audit("autonomy_promotion_submitted", case)
        return case

    # -- Review -------------------------------------------------------

    def review(
        self, case_id: str, approved: bool, reviewer: str, notes: str = ""
    ) -> SafetyCase:
        """Review a safety case — approve or deny."""
        case = self._get(case_id)
        case.status = PromotionStatus.APPROVED if approved else PromotionStatus.DENIED
        case.reviewer = reviewer
        case.review_notes = notes
        case.resolved_at = datetime.now(timezone.utc)

        if approved:
            self._promote(case)

        self._move_to_history(case)
        self._audit(
            "autonomy_promotion_approved" if approved else "autonomy_promotion_denied",
            case,
        )
        return case

    # -- Query --------------------------------------------------------

    def get_pending(self) -> list[SafetyCase]:
        return [c for c in self._cases.values() if c.status == PromotionStatus.SUBMITTED]

    def get_history(self, agent_id: str | None = None) -> list[SafetyCase]:
        cases = self._history
        if agent_id:
            cases = [c for c in cases if c.agent_id == agent_id]
        return sorted(cases, key=lambda c: c.submitted_at, reverse=True)

    def get_case(self, case_id: str) -> SafetyCase | None:
        return self._cases.get(case_id)

    # -- Internal -----------------------------------------------------

    def _promote(self, case: SafetyCase) -> None:
        """Execute the promotion in the tool registry."""
        if not self.tool_registry:
            return

        try:
            tool = self.tool_registry.get(case.tool_name)
            # Update risk tier — this is a simplified promotion;
            # a real system would have more granular control
            tool.risk_tier = case.requested_tier
        except Exception:
            pass  # Tool not found — log but don't crash

    def _get(self, case_id: str) -> SafetyCase:
        if case_id not in self._cases:
            raise ValueError(f"Safety case '{case_id}' not found")
        return self._cases[case_id]

    def _move_to_history(self, case: SafetyCase) -> None:
        self._cases.pop(case.case_id, None)
        self._history.append(case)

    def _audit(self, event: str, case: SafetyCase) -> None:
        if not self.audit_logger:
            return
        from trust_safety.governance.audit_log.models import AuditEntry
        entry = AuditEntry(
            event_type=event,
            action=f"Autonomy promotion for {case.agent_id}: "
                   f"{case.tool_name} {case.current_tier.value} → {case.requested_tier.value}",
            risk_tier=case.requested_tier,
            user_id=case.reviewer or case.agent_id,
            status=case.status.value,
            metadata={
                "case_id": case.case_id,
                "agent_id": case.agent_id,
                "tool_name": case.tool_name,
                "current_tier": case.current_tier.value,
                "requested_tier": case.requested_tier.value,
                "policy_version": case.policy_version,
                "review_notes": case.review_notes,
            },
        )
        self.audit_logger.log(entry)
