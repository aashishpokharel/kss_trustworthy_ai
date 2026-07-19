"""
FastAPI dependency injection — cached singletons for every service.

Each dependency returns the same instance for the lifetime of the
process, so all route handlers share the same audit log, tool registry,
and policy registry.
"""

from functools import lru_cache
from pathlib import Path

from fastapi import Depends

from trust_safety.config import Settings, get_settings
from trust_safety.governance.audit_log.store import (
    AppendOnlyFileStore,
    AuditLogger,
)
from trust_safety.orchestrator.tool_registry import (
    RiskTier,
    ToolDefinition,
    ToolRegistry,
)
from trust_safety.policies.registry import PolicyRegistry


# -- Settings ---------------------------------------------------------
# (delegates to the module-level lru_cache in config.py)

def get_settings_dep() -> Settings:
    """FastAPI dependency: cached Settings singleton."""
    return get_settings()


# -- Audit logger -----------------------------------------------------

@lru_cache
def _build_audit_logger() -> AuditLogger:
    """Build and cache the AuditLogger."""
    from trust_safety.config import get_settings as _get_settings
    path = str(_get_settings().audit_log_path)
    store = AppendOnlyFileStore(Path(path))
    return AuditLogger(store)


def get_audit_logger(
    settings: Settings = Depends(get_settings_dep),
) -> AuditLogger:
    """FastAPI dependency: cached AuditLogger singleton."""
    return _build_audit_logger()


# -- Tool registry ----------------------------------------------------

@lru_cache
def _build_tool_registry() -> ToolRegistry:
    """Build and cache the ToolRegistry, pre-seeded with sample tools."""
    registry = ToolRegistry()

    # Register a few sample tools to demonstrate the registry
    sample_tools = [
        ToolDefinition(
            name="read_file",
            description="Read the contents of a file.",
            risk_tier=RiskTier.LOW,
            reversible=True,
            allowed_roles=["admin", "developer", "viewer"],
            parameter_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read."}
                },
                "required": ["path"],
            },
        ),
        ToolDefinition(
            name="search_code",
            description="Search for patterns in the codebase.",
            risk_tier=RiskTier.LOW,
            reversible=True,
            allowed_roles=["admin", "developer", "viewer"],
            parameter_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern."},
                    "path": {"type": "string", "description": "Directory to search."},
                },
                "required": ["pattern"],
            },
        ),
        ToolDefinition(
            name="write_file",
            description="Write content to a file.",
            risk_tier=RiskTier.MEDIUM,
            reversible=True,
            allowed_roles=["admin", "developer"],
            parameter_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write."},
                    "content": {"type": "string", "description": "Content to write."},
                },
                "required": ["path", "content"],
            },
        ),
        ToolDefinition(
            name="execute_command",
            description="Execute a system command.",
            risk_tier=RiskTier.HIGH,
            reversible=False,
            allowed_roles=["admin"],
            rate_limit_per_minute=10,
            timeout_seconds=60,
            parameter_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to run."},
                },
                "required": ["command"],
            },
        ),
        ToolDefinition(
            name="delete_file",
            description="Delete a file permanently.",
            risk_tier=RiskTier.CRITICAL,
            reversible=False,
            allowed_roles=["admin"],
            rate_limit_per_minute=5,
            timeout_seconds=30,
            parameter_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to delete."},
                },
                "required": ["path"],
            },
        ),
        ToolDefinition(
            name="send_email",
            description="Send an external email.",
            risk_tier=RiskTier.HIGH,
            reversible=False,
            allowed_roles=["admin"],
            rate_limit_per_minute=5,
            parameter_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient address."},
                    "subject": {"type": "string", "description": "Email subject."},
                    "body": {"type": "string", "description": "Email body."},
                },
                "required": ["to", "subject", "body"],
            },
        ),
    ]

    for tool in sample_tools:
        registry.register(tool)

    return registry


def get_tool_registry(
    settings: Settings = Depends(get_settings_dep),
) -> ToolRegistry:
    """FastAPI dependency: cached ToolRegistry singleton."""
    return _build_tool_registry()


# -- Policy registry --------------------------------------------------

@lru_cache
def _build_policy_registry() -> PolicyRegistry:
    """Build and cache the PolicyRegistry."""
    return PolicyRegistry()


def get_policy_registry(
    settings: Settings = Depends(get_settings_dep),
) -> PolicyRegistry:
    """FastAPI dependency: cached PolicyRegistry singleton."""
    return _build_policy_registry()


# -- Input guardrails pipeline -----------------------------------------

from trust_safety.guardrails.input.pipeline import InputGuardrailPipeline  # noqa: E402


@lru_cache
def _build_input_pipeline() -> InputGuardrailPipeline:
    """Build and cache the InputGuardrailPipeline."""
    logger = _build_audit_logger()
    return InputGuardrailPipeline(audit_logger=logger)


def get_input_pipeline(
    settings: Settings = Depends(get_settings_dep),
) -> InputGuardrailPipeline:
    """FastAPI dependency: cached InputGuardrailPipeline singleton."""
    return _build_input_pipeline()


# -- Output guardrails pipeline ---------------------------------------

from trust_safety.guardrails.output.pipeline import OutputGuardrailPipeline  # noqa: E402


@lru_cache
def _build_output_pipeline() -> OutputGuardrailPipeline:
    """Build and cache the OutputGuardrailPipeline."""
    logger = _build_audit_logger()
    return OutputGuardrailPipeline(audit_logger=logger)


def get_output_pipeline(
    settings: Settings = Depends(get_settings_dep),
) -> OutputGuardrailPipeline:
    """FastAPI dependency: cached OutputGuardrailPipeline singleton."""
    return _build_output_pipeline()


# -- HITL Approval Queue ----------------------------------------------

from trust_safety.orchestrator.approval_queue import ApprovalQueue  # noqa: E402


@lru_cache
def _build_approval_queue() -> ApprovalQueue:
    """Build and cache the ApprovalQueue."""
    logger = _build_audit_logger()
    return ApprovalQueue(timeout_seconds=300, audit_logger=logger)


def get_approval_queue(
    settings: Settings = Depends(get_settings_dep),
) -> ApprovalQueue:
    """FastAPI dependency: cached ApprovalQueue singleton."""
    return _build_approval_queue()


# -- Circuit Breaker --------------------------------------------------

from trust_safety.orchestrator.circuit_breaker import CircuitBreaker  # noqa: E402


@lru_cache
def _build_circuit_breaker() -> CircuitBreaker:
    """Build and cache the CircuitBreaker."""
    logger = _build_audit_logger()
    return CircuitBreaker(audit_logger=logger)


def get_circuit_breaker(
    settings: Settings = Depends(get_settings_dep),
) -> CircuitBreaker:
    """FastAPI dependency: cached CircuitBreaker singleton."""
    return _build_circuit_breaker()


# -- Governance Dashboard ---------------------------------------------

from trust_safety.governance.dashboard import MetricsCollector  # noqa: E402


@lru_cache
def _build_metrics_collector() -> MetricsCollector:
    """Build and cache the MetricsCollector."""
    logger = _build_audit_logger()
    return MetricsCollector(logger)


def get_metrics_collector(
    settings: Settings = Depends(get_settings_dep),
) -> MetricsCollector:
    """FastAPI dependency: cached MetricsCollector singleton."""
    return _build_metrics_collector()


# -- LLM Provider Router + Orchestrator ---------------------------------

from trust_safety.llm.router import ProviderRouter, RoutingPolicy  # noqa: E402
from trust_safety.llm.models import LLMConfig  # noqa: E402
from trust_safety.llm.mock_client import MockLLMClient  # noqa: E402
from trust_safety.llm.orchestrator import LLMOrchestrator  # noqa: E402


@lru_cache
def _build_llm_router() -> ProviderRouter:
    """Build the ProviderRouter based on current settings."""
    from trust_safety.config import get_settings as _get_settings
    s = _get_settings()

    primary = MockLLMClient(LLMConfig(provider="mock", model="mock-model"))
    secondary = None

    # Build Anthropic client if configured
    if s.anthropic_api_key:
        from trust_safety.llm.anthropic_client import AnthropicLLMClient
        primary = AnthropicLLMClient(LLMConfig(
            provider="anthropic",
            api_key=s.anthropic_api_key,
            base_url=s.anthropic_base_url,
            model=s.anthropic_model,
            max_tokens=s.anthropic_max_tokens,
            temperature=s.anthropic_temperature,
            timeout_seconds=s.anthropic_timeout_seconds,
            max_retries=s.anthropic_max_retries,
            cost_ceiling_daily_usd=s.anthropic_cost_ceiling_daily_usd,
            zero_retention_enabled=s.anthropic_zero_retention,
        ))

    # Build DeepSeek client if configured
    if s.deepseek_api_key:
        from trust_safety.llm.deepseek_client import DeepSeekLLMClient
        ds_client = DeepSeekLLMClient(LLMConfig(
            provider="deepseek",
            api_key=s.deepseek_api_key,
            base_url=s.deepseek_base_url,
            model=s.deepseek_model,
            max_tokens=s.deepseek_max_tokens,
            temperature=s.deepseek_temperature,
            timeout_seconds=s.deepseek_timeout_seconds,
            max_retries=s.deepseek_max_retries,
            cost_ceiling_daily_usd=s.deepseek_cost_ceiling_daily_usd,
            zero_retention_enabled=s.deepseek_zero_retention,
        ))
        if isinstance(primary, MockLLMClient):
            primary = ds_client
        else:
            secondary = ds_client

    return ProviderRouter(
        primary=primary,
        secondary=secondary,
        policy=RoutingPolicy(s.llm_routing_policy),
        default_provider=s.llm_provider if s.llm_provider != "mock" else primary.provider_name,
    )


def get_llm_router(
    settings: Settings = Depends(get_settings_dep),
) -> ProviderRouter:
    return _build_llm_router()


@lru_cache
def _build_orchestrator() -> LLMOrchestrator:
    input_pipe = _build_input_pipeline()
    output_pipe = _build_output_pipeline()
    router = _build_llm_router()
    approval_q = _build_approval_queue()
    logger = _build_audit_logger()
    return LLMOrchestrator(
        input_pipeline=input_pipe,
        output_pipeline=output_pipe,
        router=router,
        approval_queue=approval_q,
        audit_logger=logger,
    )


def get_orchestrator(
    settings: Settings = Depends(get_settings_dep),
) -> LLMOrchestrator:
    return _build_orchestrator()
