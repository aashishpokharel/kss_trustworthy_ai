"""Tests for PromotionTracker — autonomy promotion workflow (Section 9.1)."""

from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from trust_safety.orchestrator.autonomy_promotion import (
    PromotionStatus,
    PromotionTracker,
)
from trust_safety.orchestrator.tool_registry import RiskTier


class TestPromotionTracker:
    """Formal autonomy promotion workflow."""

    def test_submit_safety_case(self):
        tracker = PromotionTracker()
        case = tracker.submit_case(
            agent_id="agent-1",
            tool_name="write_file",
            current_tier=RiskTier.MEDIUM,
            requested_tier=RiskTier.LOW,
            evidence={"safe_interactions": 500, "eval_block_rate": 1.0},
        )
        assert case.status == PromotionStatus.SUBMITTED
        assert case.agent_id == "agent-1"
        assert case.requested_tier == RiskTier.LOW

    def test_approve_promotion(self):
        tracker = PromotionTracker()
        case = tracker.submit_case(
            agent_id="agent-2",
            tool_name="read_file",
            current_tier=RiskTier.LOW,
            requested_tier=RiskTier.LOW,  # Same tier, just testing
        )
        result = tracker.review(case.case_id, approved=True, reviewer="security-team")
        assert result.status == PromotionStatus.APPROVED
        assert result.reviewer == "security-team"

    def test_deny_promotion(self):
        tracker = PromotionTracker()
        case = tracker.submit_case(
            agent_id="agent-3",
            tool_name="execute_command",
            current_tier=RiskTier.HIGH,
            requested_tier=RiskTier.LOW,
        )
        result = tracker.review(
            case.case_id, approved=False, reviewer="sec-ops",
            notes="Insufficient evidence — need 1000 safe interactions, got 50",
        )
        assert result.status == PromotionStatus.DENIED
        assert "50" in result.review_notes

    def test_get_pending(self):
        tracker = PromotionTracker()
        tracker.submit_case("a1", "tool_a", RiskTier.HIGH, RiskTier.MEDIUM)
        tracker.submit_case("a2", "tool_b", RiskTier.MEDIUM, RiskTier.LOW)
        assert len(tracker.get_pending()) == 2

    def test_pending_cleared_after_review(self):
        tracker = PromotionTracker()
        case = tracker.submit_case("a1", "tool", RiskTier.HIGH, RiskTier.MEDIUM)
        tracker.review(case.case_id, approved=True, reviewer="op")
        assert len(tracker.get_pending()) == 0

    def test_get_history(self):
        tracker = PromotionTracker()
        c1 = tracker.submit_case("a1", "tool_a", RiskTier.HIGH, RiskTier.MEDIUM)
        c2 = tracker.submit_case("a1", "tool_a", RiskTier.MEDIUM, RiskTier.LOW)
        tracker.review(c1.case_id, approved=True, reviewer="op")
        tracker.review(c2.case_id, approved=False, reviewer="op")
        history = tracker.get_history(agent_id="a1")
        assert len(history) == 2

    def test_audit_logged(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        tracker = PromotionTracker(audit_logger=logger)
        case = tracker.submit_case("agent-x", "tool_x", RiskTier.HIGH, RiskTier.MEDIUM)
        tracker.review(case.case_id, approved=True, reviewer="op")
        entries = list(store.read_all())
        assert len(entries) >= 2
        assert any("submitted" in e.event_type for e in entries)
        assert any("approved" in e.event_type for e in entries)

    def test_nonexistent_case_raises(self):
        tracker = PromotionTracker()
        try:
            tracker.review("nonexistent", approved=True, reviewer="op")
            assert False, "Should have raised"
        except ValueError:
            pass
