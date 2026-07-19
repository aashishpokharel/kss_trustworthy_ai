"""Data models for output guardrail findings (Sections 7, 10, 11)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from trust_safety.guardrails.input.models import PIIResult
from trust_safety.models.base import DataTier

# ------------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------------

class SchemaValidationResult(BaseModel):
    """Result of validating LLM output against a JSON Schema."""

    passed: bool = Field(description="Did the output conform to the schema?")
    errors: list[str] = Field(default_factory=list, description="Validation errors.")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warnings.")
    retry_prompt: str | None = Field(
        default=None,
        description="Corrective re-prompt to feed back to the LLM on failure "
                    "(Section 7 — retry-on-failure with corrective re-prompting).",
    )
    extracted_json: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="The parsed JSON if validation passed.",
    )


# ------------------------------------------------------------------
# Groundedness / hallucination
# ------------------------------------------------------------------

class GroundednessResult(BaseModel):
    """Result of hallucination / faithfulness checking (Section 11)."""

    score: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Groundedness score. 1.0 = all claims supported, 0.0 = no claims supported.",
    )
    total_claims: int = Field(default=0, description="Number of factual claims extracted.")
    supported_claims: int = Field(default=0, description="Claims supported by source context.")
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims that could NOT be verified against source context.",
    )
    citation_density: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Ratio of cited claims to total claims.",
    )
    hedging_detected: bool = Field(
        default=False,
        description="Did the output contain uncertainty markers?",
    )
    hedging_phrases: list[str] = Field(
        default_factory=list,
        description="Specific hedging phrases found.",
    )
    passed: bool = Field(
        default=True,
        description="Did this pass the groundedness threshold for the domain?",
    )
    domain_threshold: float = Field(
        default=0.7,
        description="The threshold that was applied.",
    )


# ------------------------------------------------------------------
# Refusal classification
# ------------------------------------------------------------------

RefusalType = Literal[
    "policy_violation",
    "capability_limit",
    "needs_clarification",
    "escalate_to_human",
    "none",
]


class RefusalClassification(BaseModel):
    """Classification of a refusal response (Section 10)."""

    is_refusal: bool = Field(
        default=False,
        description="Is the output any form of refusal or decline?",
    )
    refusal_type: RefusalType = Field(
        default="none",
        description="Which refusal category does this fall into?",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How confident is the classifier in this classification?",
    )
    over_refusal: bool = Field(
        default=False,
        description="Is this a refusal of a benign/legitimate request?  "
                    "Tracked as a first-class metric (Section 10).",
    )
    safe_alternative: str | None = Field(
        default=None,
        description="Suggested safe alternative or redirection, if applicable.",
    )


# ------------------------------------------------------------------
# Aggregate report
# ------------------------------------------------------------------

DomainType = Literal["general", "medical", "legal", "financial", "creative"]


class OutputGuardrailReport(BaseModel):
    """Complete result of the output guardrails pipeline."""

    report_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # -- Overall decision ------------------------------------------------
    allowed: bool = Field(default=True)
    block_reason: str | None = None

    # -- Per-detector results --------------------------------------------
    schema_validation: SchemaValidationResult | None = None
    groundedness: GroundednessResult | None = None
    pii_leak: PIIResult | None = None
    refusal: RefusalClassification | None = None

    # -- Metadata --------------------------------------------------------
    detectors_run: list[str] = Field(default_factory=list)
    total_latency_ms: float = 0.0
