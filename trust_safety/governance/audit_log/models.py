"""
Audit log data models.

AuditEntry is the core record — every guardrail decision, tool call,
LLM invocation, HITL approval, and policy violation is written as one
immutable entry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from trust_safety.models.base import DataTier
from trust_safety.models.context import ProvenanceTag
from trust_safety.orchestrator.tool_registry import RiskTier


class AuditEntry(BaseModel):
    """A single immutable record in the audit log.

    Every entry is linked to its predecessor via a SHA-256 hash chain
    (see AppendOnlyFileStore).  ``entry_hash`` is computed by the store,
    not by the caller — this prevents bogus hash injection.

    Fields are deliberately broad: the audit log must capture enough
    context to reconstruct *why* a decision was made, not just *what*.
    """

    # -- Identity -------------------------------------------------------
    entry_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="UUID v4, generated on creation.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this entry was written.",
    )

    # -- What happened --------------------------------------------------
    event_type: str = Field(
        ...,
        description="Event category: 'llm_call', 'tool_call', "
                    "'policy_violation', 'hitl_approval', 'hitl_denial', "
                    "'red_team_finding', 'config_change'.",
    )
    action: str = Field(
        ..., description="Human-readable description of the action."
    )
    resource: str | None = Field(
        default=None, description="Resource accessed or modified."
    )

    # -- Who ------------------------------------------------------------
    agent_id: str | None = Field(
        default=None, description="Which agent performed this action."
    )
    user_id: str | None = Field(
        default=None, description="Which human user triggered this."
    )
    session_id: str | None = Field(
        default=None, description="Session identifier for correlation."
    )

    # -- Risk & classification ------------------------------------------
    risk_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Risk score 0.0–1.0."
    )
    risk_tier: RiskTier | None = Field(
        default=None, description="Tool risk tier if applicable."
    )
    data_tier: DataTier | None = Field(
        default=None, description="Highest data classification involved."
    )

    # -- Provenance -----------------------------------------------------
    provenance: ProvenanceTag | None = Field(
        default=None, description="Provenance of the triggering context."
    )

    # -- Governance -----------------------------------------------------
    compliance_profile: str | None = Field(
        default=None, description="Active compliance profile at the time."
    )
    policy_version: str | None = Field(
        default=None,
        description="Version of the policy document in effect "
                    "(for traceability — Section 13).",
    )

    # -- Outcome --------------------------------------------------------
    status: str = Field(
        default="allowed",
        description="Outcome: 'allowed', 'blocked', 'flagged', "
                    "'pending_approval', 'approved', 'denied'.",
    )

    # -- Extensible metadata --------------------------------------------
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible key-value store for domain-specific data.",
    )

    # -- Hash chain fields (populated by the store, not the caller) -----
    previous_hash: str = Field(
        default="",
        description="SHA-256 hex of the previous entry's entry_hash.  "
                    "Empty for the first entry in the log.",
    )
    entry_hash: str = Field(
        default="",
        description="SHA-256(previous_hash + canonical_json_of_this_entry).  "
                    "Computed by AppendOnlyFileStore — do NOT set manually.",
    )

    def to_canonical_json(self) -> str:
        """Serialize the entry WITHOUT ``entry_hash`` for hash computation.

        Uses sorted keys for deterministic output.
        """
        return self.model_dump_json(
            exclude={"entry_hash"},
            # Pydantic doesn't have sort_keys; we handle ordering at the
            # serialization layer in the store.
        )


class AuditQuery(BaseModel):
    """Filter parameters for querying the audit log."""

    start_time: datetime | None = Field(
        default=None, description="Earliest timestamp to include."
    )
    end_time: datetime | None = Field(
        default=None, description="Latest timestamp to include."
    )
    user_id: str | None = Field(
        default=None, description="Filter by user."
    )
    event_type: str | None = Field(
        default=None, description="Filter by event type."
    )
    risk_score_min: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Minimum risk score threshold.",
    )
    status: str | None = Field(
        default=None, description="Filter by outcome status."
    )
    limit: int = Field(
        default=100, ge=1, le=10000, description="Max entries to return."
    )
    offset: int = Field(
        default=0, ge=0, description="Number of entries to skip."
    )
