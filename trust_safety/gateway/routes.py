"""
API routes for the Trust & Safety governance plane.

All endpoints are read-only except for audit-log writes and tool
registration (which are idempotent appends, never mutates existing data).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from trust_safety.config import Settings, get_settings
from trust_safety.gateway.dependencies import (
    get_approval_queue,
    get_audit_logger,
    get_circuit_breaker,
    get_input_pipeline,
    get_llm_router,
    get_metrics_collector,
    get_orchestrator,
    get_output_pipeline,
    get_policy_registry,
    get_tool_registry,
)
from trust_safety.governance.audit_log.models import AuditEntry, AuditQuery
from trust_safety.governance.audit_log.store import AuditLogger
from trust_safety.guardrails.input.pipeline import InputGuardrailPipeline
from trust_safety.guardrails.output.pipeline import OutputGuardrailPipeline
from trust_safety.models.base import DataTier
from trust_safety.models.context import ContextBlock, ProvenanceTag, TrustLevelEnum
from trust_safety.orchestrator.tool_registry import (
    DuplicateToolError,
    ToolDefinition,
    ToolNotFoundError,
    ToolRegistry,
)
from trust_safety.policies.registry import ComplianceProfile, PolicyRegistry

router = APIRouter(prefix="/api/v1", tags=["trust-safety"])


# ==================================================================
# Health
# ==================================================================

@router.get("/health")
async def health(
    settings: Settings = Depends(get_settings),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Basic health check — returns version and audit log entry count."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.environment.value,
        "audit_log_entries": audit_logger.count(),
    }


# ==================================================================
# Audit log
# ==================================================================

@router.post("/audit/log", status_code=status.HTTP_201_CREATED)
async def create_audit_entry(
    entry: AuditEntry,
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Append an entry to the audit log.

    The caller should NOT set ``entry_hash`` or ``previous_hash`` —
    the store computes both.  Any value passed is overwritten.
    """
    result = await audit_logger.log_async(entry)
    return result


@router.get("/audit/query")
async def query_audit_log(
    start_time: str | None = Query(default=None, description="ISO-8601 start time."),
    end_time: str | None = Query(default=None, description="ISO-8601 end time."),
    user_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    risk_score_min: float | None = Query(default=None, ge=0.0, le=1.0),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Query the audit log with optional filters."""
    from datetime import datetime

    query = AuditQuery(
        start_time=datetime.fromisoformat(start_time) if start_time else None,
        end_time=datetime.fromisoformat(end_time) if end_time else None,
        user_id=user_id,
        event_type=event_type,
        risk_score_min=risk_score_min,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return audit_logger.query(query)


@router.get("/audit/verify")
async def verify_audit_log(
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Verify the integrity of the audit log hash chain.

    Returns an IntegrityReport with ``valid=True`` and an empty error
    list if the log is intact.
    """
    return audit_logger.verify_integrity()


# ==================================================================
# Tool registry
# ==================================================================

@router.get("/tools")
async def list_tools(
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """List all registered tools with their risk posture."""
    tools = registry.list_all()
    return [
        {
            "name": t.name,
            "description": t.description,
            "risk_tier": t.risk_tier.value,
            "reversible": t.reversible,
            "required_approval": t.required_approval,
            "hitl_mode": t.derive_hitl_mode().value,
            "allowed_roles": t.allowed_roles,
            "rate_limit_per_minute": t.rate_limit_per_minute,
        }
        for t in tools
    ]


@router.get("/tools/{name}")
async def get_tool(
    name: str,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """Get a single tool definition."""
    try:
        tool = registry.get(name)
    except ToolNotFoundError:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")
    return {
        "name": tool.name,
        "description": tool.description,
        "risk_tier": tool.risk_tier.value,
        "reversible": tool.reversible,
        "required_approval": tool.required_approval,
        "hitl_mode": tool.derive_hitl_mode().value,
        "allowed_roles": tool.allowed_roles,
        "parameter_schema": tool.parameter_schema,
        "rate_limit_per_minute": tool.rate_limit_per_minute,
        "timeout_seconds": tool.timeout_seconds,
    }


@router.post("/tools", status_code=status.HTTP_201_CREATED)
async def register_tool(
    tool: ToolDefinition,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """Register a new tool in the registry."""
    try:
        registry.register(tool)
    except DuplicateToolError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"status": "registered", "tool": tool.name}


# ==================================================================
# Policy / compliance
# ==================================================================

@router.get("/policies")
async def list_policies(
    policy_registry: PolicyRegistry = Depends(get_policy_registry),
):
    """List available compliance profiles."""
    profiles = policy_registry.list_profiles()
    return [
        {
            "name": p.name.value,
            "description": p.description,
            "pii_treatment": p.data_handling.pii_treatment,
            "restricted_tier_allowed": p.data_handling.restricted_tier_allowed,
            "max_retention_days": p.data_handling.max_retention_days,
        }
        for p in profiles
    ]


@router.get("/policies/{profile}")
async def get_policy(
    profile: str,
    policy_registry: PolicyRegistry = Depends(get_policy_registry),
):
    """Get a single compliance profile's configuration."""
    try:
        config = policy_registry.get_profile_by_name(profile)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "name": config.name.value,
        "description": config.description,
        "data_handling": config.data_handling.model_dump(),
    }


@router.post("/policies/validate-tier")
async def validate_data_tier(
    tier: str = Query(..., description="DataTier value to validate."),
    profile: str = Query(default="none", description="Compliance profile to check against."),
    policy_registry: PolicyRegistry = Depends(get_policy_registry),
):
    """Check whether a DataTier is allowed under a compliance profile."""
    try:
        data_tier = DataTier(tier)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown DataTier: '{tier}'. Known: {[t.value for t in DataTier]}",
        )
    try:
        allowed = policy_registry.validate_data_tier(
            data_tier, ComplianceProfile(profile)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"tier": tier, "profile": profile, "allowed": allowed}


# ==================================================================
# Input guardrails scan
# ==================================================================

@router.post("/guardrails/input/scan")
async def scan_input(
    text: str = Query(..., description="The input text to scan."),
    source: str = Query(default="api", description="Source of the input."),
    pipeline: InputGuardrailPipeline = Depends(get_input_pipeline),
):
    """Run the full input guardrails pipeline against *text*.

    Returns an InputGuardrailReport.  If ``allowed`` is False, the
    request should be blocked — see ``block_reason`` for details.
    """
    # Build minimal context block for provenance tracking
    provenance = ProvenanceTag(
        source_id="api-call",
        source_type="user_input",
        origin=source,
    )
    context = ContextBlock(
        content=text,
        source=source,
        trust_level=TrustLevelEnum.UNTRUSTED,
        provenance=provenance,
    )

    report = pipeline.run(text, context)
    return report.model_dump()


# ==================================================================
# Output guardrails scan
# ==================================================================

@router.post("/guardrails/output/scan")
async def scan_output(
    output_text: str = Query(..., description="The LLM output text to scan."),
    source_context: str | None = Query(default=None, description="Optional grounding context for hallucination check."),
    expected_schema_json: str | None = Query(default=None, description="Optional JSON Schema string for output validation."),
    domain: str = Query(default="general", description="Domain for groundedness thresholds."),
    input_was_benign: bool = Query(default=True, description="Was the original input known-benign?"),
    pipeline: OutputGuardrailPipeline = Depends(get_output_pipeline),
):
    """Run the full output guardrails pipeline against LLM *output_text*.

    Returns an OutputGuardrailReport.  If ``allowed`` is False, the
    output should be blocked or regenerated.
    """
    import json as _json

    expected_schema = None
    if expected_schema_json:
        try:
            expected_schema = _json.loads(expected_schema_json)
        except _json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid expected_schema_json: not valid JSON")

    report = pipeline.run(
        output_text=output_text,
        source_context=source_context,
        expected_schema=expected_schema,
        domain=domain,
        input_was_benign=input_was_benign,
    )
    return report.model_dump()


# ==================================================================
# HITL Approval Queue
# ==================================================================

from trust_safety.orchestrator.approval_queue import (  # noqa: E402
    ApprovalQueue,
    ApprovalRequest as ApprovalRequestModel,
)
from trust_safety.orchestrator.tool_registry import RiskTier  # noqa: E402


@router.post("/hitl/approval/submit", status_code=status.HTTP_201_CREATED)
async def submit_approval(
    tool_name: str = Query(..., description="Tool requiring approval."),
    tool_params_json: str = Query(default="{}", description="Tool parameters as JSON."),
    risk_tier: str = Query(default="high", description="Risk tier."),
    requester: str = Query(default="system"),
    reason: str = Query(default=""),
    queue: ApprovalQueue = Depends(get_approval_queue),
):
    """Submit a tool call for human approval."""
    import json as _json
    try:
        params = _json.loads(tool_params_json)
    except _json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid tool_params_json")

    try:
        tier = RiskTier(risk_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid risk_tier: {risk_tier}")

    req = queue.submit(tool_name, params, tier, requester, reason)
    return req.model_dump()


@router.post("/hitl/approval/{request_id}/approve")
async def approve_request(
    request_id: str,
    reviewer: str = Query(default="operator"),
    queue: ApprovalQueue = Depends(get_approval_queue),
):
    """Approve a pending approval request."""
    try:
        req = queue.approve(request_id, reviewer)
        return req.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/hitl/approval/{request_id}/deny")
async def deny_request(
    request_id: str,
    reviewer: str = Query(default="operator"),
    reason: str = Query(default=""),
    queue: ApprovalQueue = Depends(get_approval_queue),
):
    """Deny a pending approval request."""
    try:
        req = queue.deny(request_id, reviewer, reason)
        return req.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/hitl/approval/pending")
async def list_pending(
    queue: ApprovalQueue = Depends(get_approval_queue),
):
    """List all pending approval requests."""
    pending = queue.get_pending()
    return [r.model_dump() for r in pending]


@router.get("/hitl/approval/history")
async def approval_history(
    limit: int = Query(default=50),
    queue: ApprovalQueue = Depends(get_approval_queue),
):
    """List resolved approval requests."""
    history = queue.get_history(limit)
    return [r.model_dump() for r in history]


# ==================================================================
# Circuit Breaker
# ==================================================================

from trust_safety.orchestrator.circuit_breaker import (  # noqa: E402
    CircuitBreaker,
)


@router.get("/circuit-breaker/status")
async def circuit_breaker_status(
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """Get the current circuit breaker status."""
    return breaker.status().model_dump()


@router.post("/circuit-breaker/trip")
async def trip_circuit_breaker(
    reason: str = Query(..., description="Why the breaker is being tripped."),
    operator: str = Query(default="operator"),
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """TRIP the circuit breaker — halt all autonomous actions.

    This is an EMERGENCY action.  All non-read-only tool calls will be
    blocked until the breaker is reset.
    """
    return breaker.trip(reason, operator).model_dump()


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker(
    operator: str = Query(default="operator"),
    breaker: CircuitBreaker = Depends(get_circuit_breaker),
):
    """RESET the circuit breaker — resume normal operation."""
    return breaker.reset(operator).model_dump()


# ==================================================================
# Governance Dashboard
# ==================================================================

from trust_safety.governance.dashboard import MetricsCollector  # noqa: E402


@router.get("/dashboard/metrics")
async def dashboard_metrics(
    hours: int = Query(default=24, description="Time window in hours."),
    collector: MetricsCollector = Depends(get_metrics_collector),
):
    """Get governance metrics for the specified time window."""
    return collector.get_metrics(hours=hours).model_dump()


# ==================================================================
# Incident Review
# ==================================================================

from trust_safety.governance.incident_review import (  # noqa: E402
    IncidentSeverity,
    IncidentSource,
    IncidentTracker,
)


_incident_tracker: IncidentTracker | None = None


def get_incident_tracker() -> IncidentTracker:
    global _incident_tracker
    if _incident_tracker is None:
        from trust_safety.gateway.dependencies import _build_audit_logger
        _incident_tracker = IncidentTracker(audit_logger=_build_audit_logger())
    return _incident_tracker


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
async def report_incident(
    title: str = Query(..., description="Incident title."),
    description: str = Query(default=""),
    severity: str = Query(default="medium"),
    source: str = Query(default="auto_detection"),
    tracker: IncidentTracker = Depends(get_incident_tracker),
):
    """File a new security/safety incident."""
    try:
        sev = IncidentSeverity(severity)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    try:
        src = IncidentSource(source)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid source: {source}")

    incident = tracker.report(title, description, sev, src)
    return incident.model_dump()


@router.get("/incidents")
async def list_incidents(
    tracker: IncidentTracker = Depends(get_incident_tracker),
):
    """List all incidents."""
    return [i.model_dump() for i in tracker.list_all()]


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    remediation: str = Query(default=""),
    tracker: IncidentTracker = Depends(get_incident_tracker),
):
    """Resolve an incident with remediation details."""
    try:
        incident = tracker.resolve(incident_id, remediation)
        return incident.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ==================================================================
# Eval Scheduler
# ==================================================================

from trust_safety.eval.scheduler import (  # noqa: E402
    EvalCadence,
    EvalScheduler,
)

_scheduler: EvalScheduler | None = None


def get_scheduler() -> EvalScheduler:
    global _scheduler
    if _scheduler is None:
        from trust_safety.gateway.dependencies import _build_audit_logger
        _scheduler = EvalScheduler(audit_logger=_build_audit_logger())
        _scheduler.add_schedule("weekly_injection", EvalCadence.WEEKLY,
                                ["trust_safety/eval/suites/injection_suite.yaml"])
    return _scheduler


@router.get("/eval/schedules")
async def list_schedules(
    scheduler: EvalScheduler = Depends(get_scheduler),
):
    return [{"name": s.name, "cadence": s.cadence.value, "is_due": s.is_due()}
            for s in scheduler.schedules.values()]


@router.post("/eval/schedules", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    name: str = Query(...),
    cadence: str = Query(default="daily"),
    suite_paths: str = Query(default=""),
    scheduler: EvalScheduler = Depends(get_scheduler),
):
    try:
        cad = EvalCadence(cadence)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cadence: {cadence}")
    paths = [p.strip() for p in suite_paths.split(",") if p.strip()]
    schedule = scheduler.add_schedule(name, cad, paths)
    return {"name": schedule.name, "cadence": schedule.cadence.value}


@router.post("/eval/run-due")
async def run_due_evals(
    scheduler: EvalScheduler = Depends(get_scheduler),
):
    results = scheduler.run_due()
    return {name: [r.model_dump() for r in suite_results]
            for name, suite_results in results.items()}


# ==================================================================
# Policy Versioning
# ==================================================================

from trust_safety.governance.policy_versioning import (  # noqa: E402
    PolicyVersionTracker,
)

_policy_tracker: PolicyVersionTracker | None = None


def get_policy_tracker() -> PolicyVersionTracker:
    global _policy_tracker
    if _policy_tracker is None:
        from trust_safety.gateway.dependencies import _build_audit_logger
        _policy_tracker = PolicyVersionTracker(audit_logger=_build_audit_logger())
        _policy_tracker.register("constitution",
                                 "trust_safety/governance/policy_docs/constitution.md",
                                 "1.0.0", changelog=["Initial ratified version"])
    return _policy_tracker


@router.get("/policies/versions/{name}")
async def policy_version_history(
    name: str,
    tracker: PolicyVersionTracker = Depends(get_policy_tracker),
):
    history = tracker.get_history(name)
    current = tracker.get_current(name)
    return {
        "name": name,
        "current_version": current.version if current else None,
        "versions": [{"version": v.version, "changelog": v.changelog,
                       "active": v.active} for v in history],
    }


# ==================================================================
# Autonomy Promotion
# ==================================================================

from trust_safety.orchestrator.autonomy_promotion import (  # noqa: E402
    PromotionTracker,
)

_promotion_tracker: PromotionTracker | None = None


def get_promotion_tracker() -> PromotionTracker:
    global _promotion_tracker
    if _promotion_tracker is None:
        from trust_safety.gateway.dependencies import _build_audit_logger
        _promotion_tracker = PromotionTracker(audit_logger=_build_audit_logger())
    return _promotion_tracker


@router.post("/autonomy/promote", status_code=status.HTTP_201_CREATED)
async def submit_promotion(
    agent_id: str = Query(...),
    tool_name: str = Query(...),
    current_tier: str = Query(...),
    requested_tier: str = Query(...),
    safe_interactions: int = Query(default=0),
    eval_block_rate: float = Query(default=0.0),
    tracker: PromotionTracker = Depends(get_promotion_tracker),
):
    try:
        cur = RiskTier(current_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid current_tier: {current_tier}")
    try:
        req = RiskTier(requested_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid requested_tier: {requested_tier}")
    case = tracker.submit_case(agent_id, tool_name, cur, req,
                               {"safe_interactions": safe_interactions,
                                "eval_block_rate": eval_block_rate})
    return case.model_dump()


@router.get("/autonomy/promote/pending")
async def pending_promotions(
    tracker: PromotionTracker = Depends(get_promotion_tracker),
):
    return [c.model_dump() for c in tracker.get_pending()]


@router.post("/autonomy/promote/{case_id}/review")
async def review_promotion(
    case_id: str,
    approved: bool = Query(default=True),
    reviewer: str = Query(default="security-team"),
    notes: str = Query(default=""),
    tracker: PromotionTracker = Depends(get_promotion_tracker),
):
    try:
        case = tracker.review(case_id, approved, reviewer, notes)
        return case.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/dashboard/summary")
async def dashboard_summary(
    collector: MetricsCollector = Depends(get_metrics_collector),
):
    """Get a quick audit log summary."""
    return collector.get_summary().model_dump()


# ==================================================================
# LLM Generate (full orchestrator pipeline)
# ==================================================================

from trust_safety.llm.orchestrator import LLMOrchestrator  # noqa: E402
from trust_safety.llm.router import ProviderRouter  # noqa: E402


@router.post("/generate")
async def generate(
    user_input: str = Query(..., description="User input text."),
    source_context: str | None = Query(default=None, description="Optional RAG/retrieval context."),
    orchestrator: LLMOrchestrator = Depends(get_orchestrator),
):
    """Run the full pipeline: input guardrails → LLM → output guardrails → HITL.

    This is the main integration endpoint.  It calls the configured LLM
    provider, runs all guardrails, and returns a complete result.
    """
    result = await orchestrator.generate(
        user_input=user_input,
        source_context=source_context,
    )
    return result.model_dump()


@router.get("/llm/providers")
async def list_providers(
    router: ProviderRouter = Depends(get_llm_router),
):
    """List configured LLM providers and their status."""
    clients = router.list_clients()
    return [
        {
            "provider": c.provider_name,
            "model": c.config.model,
            "configured": c.config.is_configured,
            "zero_retention": c.config.zero_retention_enabled,
        }
        for c in clients
    ]


@router.post("/llm/providers/{name}/test")
async def test_provider(
    name: str,
    router: ProviderRouter = Depends(get_llm_router),
):
    """Test connectivity to a specific LLM provider."""
    clients = router.list_clients()
    target = next((c for c in clients if c.provider_name == name), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")

    try:
        ok = await target.health_check()
        return {"provider": name, "healthy": ok}
    except Exception as exc:
        return {"provider": name, "healthy": False, "error": str(exc)}


# ==================================================================
# CI Eval
# ==================================================================

from trust_safety.eval.ci_runner import EvalRunner  # noqa: E402


@router.post("/eval/run")
async def run_eval(
    suite_path: str = Query(
        default="trust_safety/eval/suites/injection_suite.yaml",
        description="Path to eval suite YAML.",
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Run a CI eval suite and return results.

    Fails the build (returns regression_detected=True) if metrics
    have regressed past the suite's threshold.
    """
    runner = EvalRunner(audit_logger=audit_logger)
    suite = runner.load_suite(suite_path)
    result = runner.run_suite(suite)
    return result.model_dump()


# ==================================================================
# Guardrail Test Console (llm-integration doc §8.5)
# ==================================================================

@router.post("/test-console/run")
async def test_console_run(
    user_input: str = Query(..., description="The prompt to test."),
    context_blocks: str | None = Query(default=None, description="Optional JSON array of context blocks for RAG simulation."),
    provider: str = Query(default="mock", description="Provider: mock, anthropic, or deepseek."),
    orchestrator: LLMOrchestrator = Depends(get_orchestrator),
    router: ProviderRouter = Depends(get_llm_router),
    settings: Settings = Depends(get_settings),
):
    """Run a prompt through both the guarded and unguarded paths side-by-side.

    **Hard-blocked in production** — this bypass endpoint is for testing only.
    All traffic is tagged ``source=test_console`` in the audit log.
    """
    # --- Server-side production hard-block (§8.5 critical restriction) ---
    if settings.environment.value == "production":
        raise HTTPException(
            status_code=403,
            detail="Guardrail bypass is disabled in production.",
        )

    # --- Parse context blocks ---
    import json as _json
    blocks = []
    if context_blocks:
        try:
            blocks = _json.loads(context_blocks)
        except _json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid context_blocks JSON")

    # --- PATH A: With guardrails (full orchestrator) ---
    guarded_result = await orchestrator.generate(
        user_input=user_input,
        source_context=context_blocks,
    )

    # --- PATH B: Without guardrails (raw LLM call, skips stages [2] and [5]) ---
    unguarded_text = ""
    unguarded_error = None
    try:
        client = router.route()
        messages = [{"role": "user", "content": user_input}]
        if blocks:
            ctx_text = "\n".join(
                b.get("content", "") for b in blocks if isinstance(b, dict)
            )
            if ctx_text:
                messages.insert(0, {"role": "user", "content": f"[CONTEXT]\n{ctx_text}\n[/CONTEXT]"})
        raw_response = await client.generate(messages)
        unguarded_text = raw_response.text
    except Exception as exc:
        unguarded_error = str(exc)

    # --- Build diff summary ---
    diffs = []
    if guarded_result.success and unguarded_text:
        if guarded_result.response_text != unguarded_text:
            diffs.append("response_text_changed")
        if guarded_result.response_text == "" and unguarded_text:
            diffs.append("guarded_blocked_unguarded_responded")
    elif not guarded_result.success and unguarded_text:
        diffs.append("guarded_blocked_unguarded_responded")

    # --- Audit log: tag as test_console ---
    from trust_safety.governance.audit_log.models import AuditEntry
    if orchestrator.audit_logger:
        orchestrator.audit_logger.log(AuditEntry(
            event_type="test_console_run",
            action=f"Test console: guarded={'pass' if guarded_result.success else 'blocked'} | provider={provider}",
            user_id="test_console",
            status="allowed",
            metadata={
                "source": "test_console",
                "provider": provider,
                "guarded_success": guarded_result.success,
                "guarded_block_reason": guarded_result.block_reason,
                "unguarded_has_response": bool(unguarded_text),
                "unguarded_error": unguarded_error,
                "diffs": diffs,
            },
        ))

    return {
        "guarded": guarded_result.model_dump(),
        "unguarded": {
            "text": unguarded_text,
            "error": unguarded_error,
        },
        "diff": diffs,
        "provider": provider,
        "source": "test_console",
    }
