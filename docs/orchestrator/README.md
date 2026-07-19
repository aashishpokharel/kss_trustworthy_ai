# Orchestrator Module

## 1. Purpose

Stage [3] of the pipeline. Manages tool registration, HITL approval routing, policy enforcement, circuit breaking, autonomy promotion, and — in production — the decision to route to the LLM. Architecture doc: Sections 9, 9.2.

## 2. Public Interface

### Tool Registry

**`ToolRegistry`** — `trust_safety/orchestrator/tool_registry.py`

| Method | Signature | Description |
|---|---|---|
| `register(tool)` | `tool: ToolDefinition` → `None` | Register a tool. Raises `DuplicateToolError` on name conflict. |
| `get(name)` | `name: str` → `ToolDefinition` | Look up a tool. Raises `ToolNotFoundError`. |
| `list_all()` | → `list[ToolDefinition]` | All registered tools. |
| `list_by_risk(tier)` | `tier: RiskTier` → `list[ToolDefinition]` | Filter by risk tier. |
| `check_permission(tool_name, role)` | `str, str` → `PermissionResult` | Check if role can invoke tool. Returns HITL mode. |
| `get_required_hitl_mode(tool_name)` | `str` → `HitlMode` | Derived HITL mode for a tool. |

**`ToolDefinition`** fields: `name, description, risk_tier, reversible, required_approval, parameter_schema, rate_limit_per_minute, timeout_seconds, allowed_roles`.

**HITL derivation** (`derive_hitl_mode()`):
| Risk Tier | Reversible? | HITL Mode |
|---|---|---|
| LOW | any | HUMAN_OUT_OF_THE_LOOP |
| MEDIUM | yes | HUMAN_ON_THE_LOOP |
| MEDIUM | no | HUMAN_IN_THE_LOOP |
| HIGH | any | HUMAN_IN_THE_LOOP |
| CRITICAL | any | HUMAN_IN_THE_LOOP |

### Policy Gate

**`PolicyGate`** — `trust_safety/orchestrator/policy_gate.py`

| Method | Signature | Description |
|---|---|---|
| `evaluate(tool_name, params, role, submit_approval)` | `str, dict, str, bool=False` → `GateResult` | Check breaker → permission → validation → HITL. Returns `allow/deny/require_approval`. |

### Approval Queue

**`ApprovalQueue`** — `trust_safety/orchestrator/approval_queue.py`

| Method | Signature | Description |
|---|---|---|
| `submit(tool_name, tool_params, risk_tier, requester, reason)` | `str, dict, RiskTier, str, str` → `ApprovalRequest` | Submit for human approval. |
| `approve(request_id, reviewer)` | `str, str` → `ApprovalRequest` | Approve. Raises `ValueError` if not found/timed out. |
| `deny(request_id, reviewer, reason)` | `str, str, str` → `ApprovalRequest` | Deny. |
| `check_timeouts()` | → `list[ApprovalRequest]` | Auto-deny expired requests. **FAIL-CLOSED**: timeout = denial, never auto-approval. |
| `get_pending()` | → `list[ApprovalRequest]` | Unresolved requests. Calls `check_timeouts()` first. |
| `get_history(limit)` | `int` → `list[ApprovalRequest]` | Resolved requests, most recent first. |
| `stats()` | → `dict[str, int]` | Counts by status. |

### Circuit Breaker

**`CircuitBreaker`** — `trust_safety/orchestrator/circuit_breaker.py`

| Method | Signature | Description |
|---|---|---|
| `trip(reason, operator)` | `str, str` → `CircuitBreakerStatus` | OPEN the breaker — halt all autonomous actions. Logged at CRITICAL. |
| `reset(operator)` | `str` → `CircuitBreakerStatus` | CLOSE the breaker — resume normal operation. |
| `is_operational()` | → `bool` | False when OPEN. |
| `is_tool_allowed(tool_name)` | `str` → `bool` | When OPEN, only `ALWAYS_ALLOWED` tools (read_file, search_code, read_directory) pass. |
| `status()` | → `CircuitBreakerStatus` | Current state + trip metadata. |

### Autonomy Promotion

**`PromotionTracker`** — `trust_safety/orchestrator/autonomy_promotion.py`

| Method | Signature | Description |
|---|---|---|
| `submit_case(agent_id, tool_name, current_tier, requested_tier, evidence, policy_version)` | `str, str, RiskTier, RiskTier, dict, str` → `SafetyCase` | File a promotion safety case. |
| `review(case_id, approved, reviewer, notes)` | `str, bool, str, str` → `SafetyCase` | Approve or deny. Approval executes the promotion in the tool registry. |

## 3. Configuration

| Variable | Default | Notes |
|---|---|---|
| `TS_HITL_TIMEOUT_SECONDS` | `300` | Per-request approval timeout. Must be ≥30. |
| `TS_HITL_FAIL_CLOSED` | `True` | If True, timeout = deny. Do NOT set to False in production. |
| `TS_CANARY_FORCE_HITL` | `False` | When True, ALL tool calls require HITL approval regardless of risk tier (for canary phase). |

## 4. Data Flow

```
Tool call request → CircuitBreaker.is_tool_allowed()
                  → ToolRegistry.check_permission()
                  → ToolDefinition.validate_params()
                  → If HITL required → ApprovalQueue.submit()
                  → GateResult
```

**This module does NOT:**
- Execute tools (that's stage [6] — the Action/Tool Layer, outside current scope)
- Handle LLM API failure (that's `llm/retry.py`)
- Enforce rate limits at runtime (declared in ToolDefinition, enforced by external layer)

## 5. Dependencies

- **Internal**: `trust_safety.governance.audit_log` (all approval/breaker/promotion events are logged)
- **External**: None beyond stdlib + pydantic.

## 6. Usage Example

```python
from trust_safety.orchestrator import ToolRegistry, RiskTier, ToolDefinition
from trust_safety.orchestrator.approval_queue import ApprovalQueue
from trust_safety.orchestrator.circuit_breaker import CircuitBreaker
from trust_safety.orchestrator.policy_gate import PolicyGate

# Register tools
reg = ToolRegistry()
reg.register(ToolDefinition(name="delete_file", description="Delete a file",
    risk_tier=RiskTier.HIGH, reversible=False, allowed_roles=["admin"]))

# Set up gate
breaker = CircuitBreaker()
queue = ApprovalQueue(timeout_seconds=300)
gate = PolicyGate(registry=reg, circuit_breaker=breaker, approval_queue=queue)

# HIGH risk tool → requires approval
result = gate.evaluate("delete_file", {"path": "/tmp/x"}, "admin", submit_approval=True)
print(result.decision)  # "require_approval"
print(result.approval_request_id)  # UUID

# Approve it
req = queue.approve(result.approval_request_id, "operator-alice")
print(req.status)  # ApprovalStatus.APPROVED

# Trip the breaker — all dangerous tools blocked
breaker.trip("Suspicious activity detected", "security-team")
result = gate.evaluate("delete_file", {"path": "/tmp/x"}, "admin")
print(result.decision)  # "deny"
print(result.reason)  # "Circuit breaker is OPEN..."
```

## 7. Testing

Tests: `trust_safety/tests/test_tool_registry.py`, `test_approval_queue.py`, `test_circuit_breaker.py`, `test_policy_gate.py`, `test_autonomy_promotion.py`

Run: `pytest trust_safety/tests/test_tool_registry.py trust_safety/tests/test_approval_queue.py trust_safety/tests/test_circuit_breaker.py trust_safety/tests/test_policy_gate.py trust_safety/tests/test_autonomy_promotion.py -v`

Coverage: Full HITL lifecycle (submit→approve/deny/timeout), breaker trip/reset/state transitions, HITL derivation for all tier+reversible combos, promotion workflow, audit logging for all events.

## 8. Failure Modes

- **Approval queue timeout**: FAIL-CLOSED. Expired requests are auto-denied. Never auto-approved. `check_timeouts()` is called on every `get_pending()` and `submit()`.
- **Circuit breaker**: Independent of the LLM process. Enforced at the orchestration layer. Trip events logged at CRITICAL severity.
- **Policy gate**: FAIL-CLOSED. Permission denied → `deny`. Parameter validation failure → `deny`. Breaker open → `deny` for non-readonly tools.
- **Promotion approval**: Requires human reviewer. Audit logged. If tool registry is unavailable, promotion silently fails (logged, doesn't crash).

## 9. Related Modules

- Called by: `LLMOrchestrator`, gateway routes
- Calls: `trust_safety.governance.audit_log`
- See also: [../governance/README.md](../governance/README.md), [../llm-integration/README.md](../llm-integration/README.md)
