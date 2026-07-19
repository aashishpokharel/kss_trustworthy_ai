"""
Environment-based configuration with validation at startup.

The single source of truth for all runtime settings.  Every other module
consumes a Settings instance — no scattered os.getenv() calls.
"""

from enum import Enum
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment — controls safety-critical defaults."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Runtime settings for the Trust & Safety layer.

    All fields can be set via environment variables prefixed with ``TS_``
    (e.g. ``TS_AUDIT_LOG_PATH``, ``TS_ENVIRONMENT``).
    """

    model_config = SettingsConfigDict(
        env_prefix="TS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # -- Environment -------------------------------------------------------
    environment: Environment = Environment.DEVELOPMENT

    # -- Audit log ---------------------------------------------------------
    audit_log_path: Path = Field(
        default=Path("./data/audit_log.jsonl"),
        description="Path to the append-only JSONL audit log file.",
    )
    audit_log_verify_on_read: bool = Field(
        default=True,
        description="Verify the hash chain on every read (expensive but safe).",
    )

    # -- Policy / compliance -----------------------------------------------
    policy_profiles: list[str] = Field(
        default=["none"],
        description="Compliance profiles to activate (none, gdpr, hipaa, ccpa).",
    )

    # -- HITL (human-in-the-loop) ------------------------------------------
    hitl_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=86400,
        description="How long to wait for human approval before failing closed.",
    )
    hitl_fail_closed: bool = Field(
        default=True,
        description="If True, timeout = deny.  Never fail open.",
    )

    # -- Model -------------------------------------------------------------
    model_classifier: str = Field(
        default="",
        description="Optional auxiliary classifier model path/name for safety checks.",
    )

    # -- Trust defaults ----------------------------------------------------
    trust_level: str = Field(
        default="balanced",
        description="Default trust posture: strict, balanced, or flexible.",
    )

    # -- Feature flags -----------------------------------------------------
    enable_input_guardrails: bool = True
    enable_output_guardrails: bool = True

    # -- LLM Provider -------------------------------------------------------
    llm_provider: str = Field(
        default="mock",
        description="Active LLM provider: mock, anthropic, or deepseek.",
    )
    llm_routing_policy: str = Field(
        default="fixed_default",
        description="Provider routing policy: fixed_default, task_based, cost_based, fallback_only.",
    )

    # Anthropic / DeepSeek (via Anthropic endpoint)
    anthropic_api_key: str = Field(default="", description="Anthropic API key.")
    anthropic_base_url: str = Field(default="", description="Anthropic base URL (override for DeepSeek endpoint).")
    anthropic_model: str = Field(default="claude-sonnet-5", description="Anthropic model name.")
    anthropic_max_tokens: int = Field(default=4096, ge=1)
    anthropic_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    anthropic_timeout_seconds: int = Field(default=60, ge=5, le=600)
    anthropic_max_retries: int = Field(default=3, ge=0, le=10)
    anthropic_cost_ceiling_daily_usd: float = Field(default=50.0, ge=0.0)
    anthropic_zero_retention: bool = Field(
        default=False,
        description="Confirmed zero-retention/no-train for this provider account.",
    )

    # DeepSeek (OpenAI-compatible endpoint)
    deepseek_api_key: str = Field(default="", description="DeepSeek API key.")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek base URL.")
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek model name.")
    deepseek_max_tokens: int = Field(default=4096, ge=1)
    deepseek_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    deepseek_timeout_seconds: int = Field(default=60, ge=5, le=600)
    deepseek_max_retries: int = Field(default=3, ge=0, le=10)
    deepseek_cost_ceiling_daily_usd: float = Field(default=50.0, ge=0.0)
    deepseek_zero_retention: bool = Field(default=False)

    # -- Environment ladder -------------------------------------------------
    environment_ladder: str = Field(
        default="mock",
        description="Current rung: mock, sandbox, shadow, canary, production.",
    )
    canary_force_hitl: bool = Field(
        default=False,
        description="Force HITL-in-loop for ALL tool calls during canary phase.",
    )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_rules(self) -> list[str]:
        """Check that the current settings form a coherent, safe configuration.

        Returns a (possibly-empty) list of human-readable issues.  Called at
        app startup; the process should refuse to start if the list is
        non-empty in production.
        """
        issues: list[str] = []

        # Policy profiles must be known
        known = {"none", "gdpr", "hipaa", "ccpa"}
        unknown = set(self.policy_profiles) - known
        if unknown:
            issues.append(
                f"Unknown compliance profile(s): {unknown}. Known: {known}"
            )

        # Production safety checks
        if self.environment == Environment.PRODUCTION:
            if self.hitl_timeout_seconds > 3600:
                issues.append(
                    "HITL timeout > 1 hour in production — risk of indefinite wait"
                )
            if not self.hitl_fail_closed:
                issues.append(
                    "CRITICAL: hitl_fail_closed=False in production — "
                    "operations will proceed without approval on timeout"
                )
            if self.llm_provider == "mock":
                issues.append(
                    "CRITICAL: llm_provider=mock in production — no real LLM configured"
                )

        # Provider validation
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            issues.append("llm_provider=anthropic but anthropic_api_key is not set")
        if self.llm_provider == "deepseek" and not self.deepseek_api_key:
            issues.append("llm_provider=deepseek but deepseek_api_key is not set")

        # Environment ladder
        if self.environment_ladder in ("canary", "production") and not self.canary_force_hitl:
            issues.append(
                "canary_force_hitl should be True during canary/production "
                "ladder — all tool calls should require HITL approval"
            )

        return issues


# ------------------------------------------------------------------
# Cached singleton — FastAPI dependencies and module-level callers
# all get the same instance.
# ------------------------------------------------------------------

@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
