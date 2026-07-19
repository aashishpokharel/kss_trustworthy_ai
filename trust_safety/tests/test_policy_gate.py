"""Tests for PolicyGate — wired into CircuitBreaker + ApprovalQueue."""

from trust_safety.orchestrator.approval_queue import ApprovalQueue
from trust_safety.orchestrator.circuit_breaker import CircuitBreaker
from trust_safety.orchestrator.policy_gate import PolicyGate
from trust_safety.orchestrator.tool_registry import (
    RiskTier,
    ToolDefinition,
    ToolRegistry,
)


def make_registry() -> ToolRegistry:
    """Build a test tool registry."""
    reg = ToolRegistry()
    reg.register(ToolDefinition(
        name="read_file", description="Read a file",
        risk_tier=RiskTier.LOW, reversible=True,
        allowed_roles=["admin", "viewer"],
    ))
    reg.register(ToolDefinition(
        name="delete_file", description="Delete a file",
        risk_tier=RiskTier.HIGH, reversible=False,
        allowed_roles=["admin"],
        parameter_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    ))
    return reg


class TestPolicyGate:
    """PolicyGate with circuit breaker and approval queue."""

    def test_allow_readonly(self):
        gate = PolicyGate(registry=make_registry())
        result = gate.evaluate("read_file", {"path": "/tmp/x"}, "admin")
        assert result.decision == "allow"

    def test_deny_unauthorized_role(self):
        gate = PolicyGate(registry=make_registry())
        result = gate.evaluate("delete_file", {"path": "/tmp/x"}, "viewer")
        assert result.decision == "deny"

    def test_require_approval_for_high_risk(self):
        gate = PolicyGate(registry=make_registry())
        result = gate.evaluate("delete_file", {"path": "/tmp/x"}, "admin")
        assert result.decision == "require_approval"

    def test_require_approval_submits_to_queue(self):
        queue = ApprovalQueue()
        gate = PolicyGate(
            registry=make_registry(),
            approval_queue=queue,
        )
        result = gate.evaluate(
            "delete_file", {"path": "/tmp/x"}, "admin", submit_approval=True,
        )
        assert result.decision == "require_approval"
        assert result.approval_request_id is not None
        # Request should be in the queue
        req = queue.get_request(result.approval_request_id)
        assert req is not None
        assert req.tool_name == "delete_file"

    # -- Circuit breaker integration -----------------------------------

    def test_circuit_breaker_open_denies_dangerous(self):
        breaker = CircuitBreaker()
        breaker.trip("Emergency", "op")
        gate = PolicyGate(registry=make_registry(), circuit_breaker=breaker)
        result = gate.evaluate("delete_file", {"path": "/tmp/x"}, "admin")
        assert result.decision == "deny"
        assert "circuit breaker" in result.reason.lower()

    def test_circuit_breaker_open_allows_readonly(self):
        breaker = CircuitBreaker()
        breaker.trip("Emergency", "op")
        gate = PolicyGate(registry=make_registry(), circuit_breaker=breaker)
        result = gate.evaluate("read_file", {"path": "/tmp/x"}, "admin")
        assert result.decision == "allow"

    def test_circuit_breaker_closed_allows_all(self):
        breaker = CircuitBreaker()
        gate = PolicyGate(registry=make_registry(), circuit_breaker=breaker)
        result = gate.evaluate("delete_file", {"path": "/tmp/x"}, "admin")
        # Should still require approval (HIGH risk) but not be denied
        assert result.decision == "require_approval"

    # -- Parameter validation ------------------------------------------

    def test_invalid_params_denied(self):
        gate = PolicyGate(registry=make_registry())
        result = gate.evaluate("delete_file", {}, "admin")  # Missing required "path"
        assert result.decision == "deny"
        assert len(result.validation_errors) > 0
