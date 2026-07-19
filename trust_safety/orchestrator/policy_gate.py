"""
Policy Gate — pre-execution checkpoint for every tool call (Section 9).

Phase 3 activation: now wired into CircuitBreaker and ApprovalQueue.
Evaluation order:
1. Circuit breaker check — if OPEN, deny all but read-only tools
2. Permission check — via ToolRegistry
3. Parameter validation — via ToolDefinition.validate_params
4. HITL routing — HIGH/CRITICAL → require_approval via ApprovalQueue
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from trust_safety.orchestrator.approval_queue import ApprovalQueue, ApprovalRequest
from trust_safety.orchestrator.circuit_breaker import CircuitBreaker
from trust_safety.orchestrator.tool_registry import HitlMode, RiskTier, ToolRegistry


class GateResult(BaseModel):
    """The result of a policy-gate evaluation."""

    decision: Literal["allow", "deny", "require_approval"] = Field(
        description="The gate's decision."
    )
    reason: str = Field(default="", description="Human-readable explanation.")
    hitl_mode: HitlMode | None = Field(
        default=None, description="Required HITL mode if not denied."
    )
    approval_request_id: str | None = Field(
        default=None, description="If require_approval, the request ID for tracking."
    )
    validation_errors: list[str] = Field(default_factory=list)


class PolicyGate(BaseModel):
    """Pre-execution checkpoint for tool calls.

    Wired into:
    * CircuitBreaker — if OPEN, deny all but read-only
    * ToolRegistry — permission + HITL derivation
    * ApprovalQueue — submit for human approval when needed
    """

    model_config = {"arbitrary_types_allowed": True}

    registry: ToolRegistry
    circuit_breaker: CircuitBreaker | None = None
    approval_queue: ApprovalQueue | None = None

    def evaluate(
        self,
        tool_name: str,
        params: dict[str, Any],
        role: str,
        submit_approval: bool = False,
    ) -> GateResult:
        """Check whether *role* can invoke *tool_name* with *params*.

        Args:
            tool_name: The tool to invoke.
            params: Tool parameters.
            role: The calling user's role.
            submit_approval: If True and HITL is required, auto-submit to
                             the approval queue and return the request ID.
        """
        # 1. Circuit breaker check
        if self.circuit_breaker and not self.circuit_breaker.is_tool_allowed(tool_name):
            status = self.circuit_breaker.status()
            return GateResult(
                decision="deny",
                reason=(
                    f"Circuit breaker is OPEN.  "
                    f"Tool '{tool_name}' is blocked.  "
                    f"Reason: {status.current_trip.reason if status.current_trip else 'Unknown'}"
                ),
            )

        # 2. Permission check
        permission = self.registry.check_permission(tool_name, role)
        if not permission.allowed:
            return GateResult(
                decision="deny",
                reason=permission.reason,
            )

        # 3. Parameter validation
        try:
            tool = self.registry.get(tool_name)
        except Exception:
            return GateResult(
                decision="deny",
                reason=f"Unknown tool: '{tool_name}'",
            )

        param_errors = tool.validate_params(params)
        if param_errors:
            return GateResult(
                decision="deny",
                reason=f"Parameter validation failed for '{tool_name}'",
                validation_errors=param_errors,
            )

        # 4. HITL routing
        hitl_mode = permission.hitl_mode
        if hitl_mode == HitlMode.HUMAN_IN_THE_LOOP:
            approval_id: str | None = None
            if submit_approval and self.approval_queue:
                req = self.approval_queue.submit(
                    tool_name=tool_name,
                    tool_params=params,
                    risk_tier=tool.risk_tier,
                    requester=role,
                    reason=f"Policy gate requires approval for {tool_name}",
                )
                approval_id = req.request_id

            return GateResult(
                decision="require_approval",
                reason=(
                    f"Tool '{tool_name}' requires human approval "
                    f"(risk tier: {tool.risk_tier.value}, hitl: {hitl_mode.value})."
                ),
                hitl_mode=hitl_mode,
                approval_request_id=approval_id,
            )

        return GateResult(
            decision="allow",
            reason=f"Tool '{tool_name}' allowed ({hitl_mode.value}).",
            hitl_mode=hitl_mode,
        )
