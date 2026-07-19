"""Tests for ApprovalQueue — HITL approval lifecycle (Section 9.2)."""

import time

from trust_safety.orchestrator.approval_queue import ApprovalQueue, ApprovalStatus
from trust_safety.orchestrator.tool_registry import RiskTier


class TestApprovalQueue:
    """HITL approval queue — submit, approve, deny, timeout."""

    def test_submit_creates_pending_request(self):
        queue = ApprovalQueue()
        req = queue.submit("delete_file", {"path": "/tmp/x"}, RiskTier.HIGH)
        assert req.status == ApprovalStatus.PENDING
        assert req.tool_name == "delete_file"

    def test_approve_resolves_request(self):
        queue = ApprovalQueue()
        req = queue.submit("execute_command", {"command": "ls"}, RiskTier.HIGH)
        resolved = queue.approve(req.request_id, "operator-alice")
        assert resolved.status == ApprovalStatus.APPROVED
        assert resolved.reviewer == "operator-alice"
        assert resolved.resolved_at is not None

    def test_deny_resolves_request(self):
        queue = ApprovalQueue()
        req = queue.submit("delete_file", {"path": "/tmp/x"}, RiskTier.CRITICAL)
        resolved = queue.deny(req.request_id, "operator-bob", "Not needed")
        assert resolved.status == ApprovalStatus.DENIED
        assert resolved.denial_reason == "Not needed"

    def test_approve_nonexistent_raises(self):
        queue = ApprovalQueue()
        try:
            queue.approve("nonexistent-id", "operator")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_deny_nonexistent_raises(self):
        queue = ApprovalQueue()
        try:
            queue.deny("nonexistent-id", "operator")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_get_pending(self):
        queue = ApprovalQueue()
        queue.submit("tool_a", {}, RiskTier.HIGH)
        queue.submit("tool_b", {}, RiskTier.MEDIUM)
        pending = queue.get_pending()
        assert len(pending) == 2

    def test_pending_removed_after_approval(self):
        queue = ApprovalQueue()
        req = queue.submit("tool_a", {}, RiskTier.HIGH)
        queue.approve(req.request_id, "op")
        assert len(queue.get_pending()) == 0

    def test_get_history(self):
        queue = ApprovalQueue()
        req1 = queue.submit("tool_a", {}, RiskTier.HIGH)
        queue.approve(req1.request_id, "op")
        req2 = queue.submit("tool_b", {}, RiskTier.HIGH)
        queue.deny(req2.request_id, "op")
        history = queue.get_history()
        assert len(history) == 2

    # -- Timeout: FAIL CLOSED ------------------------------------------

    def test_timeout_auto_denies(self):
        """Expired requests must be auto-denied (fail-closed)."""
        queue = ApprovalQueue(timeout_seconds=30)  # Minimum valid timeout
        req = queue.submit("delete_file", {"path": "/tmp/x"}, RiskTier.HIGH)
        # Manually backdate the request to force timeout
        from datetime import timedelta
        req.created_at = req.created_at - timedelta(seconds=60)
        assert req.is_expired()
        timed_out = queue.check_timeouts()
        assert len(timed_out) == 1
        assert timed_out[0].status == ApprovalStatus.TIMED_OUT

    def test_timeout_occurs_before_approve(self):
        """If a request has timed out, it can't be approved afterwards."""
        queue = ApprovalQueue(timeout_seconds=30)
        req = queue.submit("tool", {}, RiskTier.HIGH)
        # Backdate past timeout
        from datetime import timedelta
        req.created_at = req.created_at - timedelta(seconds=60)
        queue.check_timeouts()  # Auto-deny it
        try:
            queue.approve(req.request_id, "op")
            assert False, "Should have raised — request timed out"
        except ValueError:
            pass

    # -- Stats ---------------------------------------------------------

    def test_stats_counts(self):
        queue = ApprovalQueue()
        req1 = queue.submit("a", {}, RiskTier.HIGH)
        req2 = queue.submit("b", {}, RiskTier.MEDIUM)
        queue.approve(req1.request_id, "op")
        queue.deny(req2.request_id, "op")
        stats = queue.stats()
        assert stats["approved"] == 1
        assert stats["denied"] == 1
        assert stats["pending"] == 0

    def test_get_request_finds_both_pending_and_history(self):
        queue = ApprovalQueue()
        req = queue.submit("tool", {}, RiskTier.HIGH)
        found = queue.get_request(req.request_id)
        assert found is not None
        assert found.status == ApprovalStatus.PENDING
        queue.approve(req.request_id, "op")
        found2 = queue.get_request(req.request_id)
        assert found2 is not None
        assert found2.status == ApprovalStatus.APPROVED
