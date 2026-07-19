"""
Data models for input guardrail findings.

Each detector produces typed findings.  The InputGuardrailReport
aggregates them all into a single pass/fail decision with structured
evidence for audit logging.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from trust_safety.models.base import DataTier

# ------------------------------------------------------------------
# Injection
# ------------------------------------------------------------------

class InjectionResult(BaseModel):
    """Result of prompt injection scanning."""

    is_injection: bool = Field(description="Did any pattern match?")
    risk_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Composite risk score from all detection layers.",
    )
    matched_patterns: list[str] = Field(
        default_factory=list,
        description="Regex patterns that matched.",
    )
    category: str = Field(
        default="none",
        description="Attack category: direct_injection, jailbreak, extraction, "
                    "impersonation, context_manipulation, encoding_trick, none.",
    )
    canary_triggered: bool = Field(
        default=False,
        description="Did the canary token appear? (Always False on input — "
                    "relevant for output-side verification.)",
    )
    heuristic_flags: list[str] = Field(
        default_factory=list,
        description="Heuristic flags raised (e.g. 'excessive_escaping', "
                    "'suspicious_length').",
    )


# ------------------------------------------------------------------
# PII
# ------------------------------------------------------------------

class PIIFinding(BaseModel):
    """A single PII entity found in the input."""

    entity_type: str = Field(description="Presidio entity type (e.g. EMAIL_ADDRESS, PHONE_NUMBER).")
    value_snippet: str = Field(description="Redacted snippet for audit (NEVER the full value).")
    start: int = Field(description="Character offset where the entity starts.")
    end: int = Field(description="Character offset where the entity ends.")
    score: float = Field(description="Presidio confidence score 0.0-1.0.")


class PIIResult(BaseModel):
    """Aggregate PII detection result."""

    pii_detected: bool = False
    findings: list[PIIFinding] = Field(default_factory=list)
    redacted_text: str | None = Field(
        default=None,
        description="Input text with all PII redacted. None if no PII found.",
    )


# ------------------------------------------------------------------
# Secrets
# ------------------------------------------------------------------

class SecretFinding(BaseModel):
    """A single secret detected in the input."""

    secret_type: str = Field(description="Type: aws_key, github_token, generic_api_key, etc.")
    match_snippet: str = Field(description="Redacted snippet (NEVER the full secret).")
    entropy: float = Field(default=0.0, description="Shannon entropy of the matched string.")
    start: int = 0
    end: int = 0


class SecretsResult(BaseModel):
    """Aggregate secrets scan result."""

    secrets_detected: bool = False
    findings: list[SecretFinding] = Field(default_factory=list)
    redacted_text: str | None = None


# ------------------------------------------------------------------
# Sensitive topics
# ------------------------------------------------------------------

SensitiveCategory = Literal[
    "weapons_cbrn",
    "cyberweapons_malware",
    "self_harm_crisis",
    "extremism",
    "csae",
    "fraud",
    "illicit_substances",
    "none",
]

RouteAction = Literal["hard_block", "safe_response", "escalate"]


class SensitiveTopicFinding(BaseModel):
    """A single sensitive topic detected."""

    category: SensitiveCategory = Field(description="Topic category.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    matched_terms: list[str] = Field(default_factory=list)
    route_action: RouteAction = Field(default="hard_block")


class SensitiveTopicResult(BaseModel):
    """Aggregate sensitive topic classification result."""

    topics_detected: bool = False
    findings: list[SensitiveTopicFinding] = Field(default_factory=list)
    strictest_action: RouteAction = Field(default="hard_block")


# ------------------------------------------------------------------
# Input validation
# ------------------------------------------------------------------

class ValidationFinding(BaseModel):
    """Input validation issues."""

    issue_type: str = Field(description="Type: homoglyph, length_exceeded, encoding, invalid_utf8.")
    detail: str = Field(description="Human-readable description of the issue.")
    blocked: bool = Field(default=True, description="Does this issue block the request?")


class ValidationResult(BaseModel):
    """Aggregate input validation result."""

    valid: bool = True
    normalized_text: str | None = None
    findings: list[ValidationFinding] = Field(default_factory=list)


# ------------------------------------------------------------------
# Aggregate report
# ------------------------------------------------------------------

class InputGuardrailReport(BaseModel):
    """The complete result of running the input guardrails pipeline.

    Every request through the pipeline produces one of these.
    It is logged to the audit log as a single entry with structured
    findings.
    """

    report_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # -- Overall decision ------------------------------------------------
    allowed: bool = Field(
        default=True,
        description="False if ANY detector blocked the input.  Fail-closed.",
    )
    block_reason: str | None = Field(
        default=None,
        description="If blocked, which detector and why.",
    )

    # -- Per-detector results --------------------------------------------
    injection: InjectionResult | None = None
    pii: PIIResult | None = None
    secrets: SecretsResult | None = None
    sensitive_topics: SensitiveTopicResult | None = None
    validation: ValidationResult | None = None

    # -- Data classification --------------------------------------------
    data_tier: DataTier | None = Field(
        default=None,
        description="Classified data tier after all detectors ran.",
    )

    # -- Metadata --------------------------------------------------------
    detectors_run: list[str] = Field(default_factory=list)
    total_latency_ms: float = 0.0
