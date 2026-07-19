"""
Governance Dashboard — metrics derived from the append-only audit log (Section 12-13).

All stats come from a single source of truth: the audit log.  No separate
metrics store.  This means every stat is fully traceable back to the raw
events that produced it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.store import AuditLogger


# ------------------------------------------------------------------
# Metrics model
# ------------------------------------------------------------------

class DashboardMetrics(BaseModel):
    """Aggregated governance metrics for a time window."""

    window_start: datetime
    window_end: datetime

    # -- Safety ----------------------------------------------------------
    total_interactions: int = 0
    blocked_interactions: int = 0
    allowed_interactions: int = 0
    block_rate: float = 0.0

    # -- Injection -------------------------------------------------------
    injection_attempts: int = 0
    injection_blocked: int = 0

    # -- PII -------------------------------------------------------------
    pii_detections_input: int = 0
    pii_leaks_output: int = 0

    # -- Secrets ---------------------------------------------------------
    secrets_detected: int = 0

    # -- Groundedness ----------------------------------------------------
    groundedness_avg: float = 0.0
    groundedness_samples: int = 0

    # -- Refusal ---------------------------------------------------------
    refusal_count: int = 0
    refusal_rate: float = 0.0
    over_refusal_count: int = 0

    # -- HITL ------------------------------------------------------------
    hitl_pending: int = 0
    hitl_approved: int = 0
    hitl_denied: int = 0
    hitl_timed_out: int = 0

    # -- Circuit breaker -------------------------------------------------
    breaker_trips: int = 0


class AuditSummary(BaseModel):
    """Quick summary of the audit log state."""

    total_entries: int = 0
    first_entry_at: datetime | None = None
    last_entry_at: datetime | None = None
    integrity_valid: bool = True
    integrity_errors: int = 0
    unique_event_types: list[str] = Field(default_factory=list)
    top_actions: list[dict[str, Any]] = Field(default_factory=list)


# ------------------------------------------------------------------
# MetricsCollector
# ------------------------------------------------------------------

class MetricsCollector:
    """Compute governance metrics from the audit log.

    Usage::

        collector = MetricsCollector(audit_logger)
        metrics = collector.get_metrics(hours=24)
        summary = collector.get_summary()
    """

    def __init__(self, audit_logger: AuditLogger) -> None:
        self._logger = audit_logger

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_metrics(self, hours: int = 24) -> DashboardMetrics:
        """Compute metrics for the last *hours* hours."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=hours)
        entries = list(self._logger.read_all())

        metrics = DashboardMetrics(
            window_start=window_start,
            window_end=now,
        )

        # Filter to window
        window_entries = [
            e for e in entries
            if e.timestamp >= window_start
        ]
        metrics.total_interactions = len(window_entries)

        groundedness_scores: list[float] = []
        event_types: dict[str, int] = {}

        for entry in window_entries:
            # Count event types
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1

            # Blocked vs allowed
            if entry.status == "blocked":
                metrics.blocked_interactions += 1
            else:
                metrics.allowed_interactions += 1

            # Injection
            if entry.event_type == "input_guardrail":
                meta = entry.metadata or {}
                if meta.get("injection_category") and meta["injection_category"] != "none":
                    metrics.injection_attempts += 1
                    if entry.status == "blocked":
                        metrics.injection_blocked += 1

            # PII
            if entry.event_type == "input_guardrail":
                if (entry.metadata or {}).get("pii_count", 0) > 0:
                    metrics.pii_detections_input += 1
            if entry.event_type == "output_guardrail":
                if (entry.metadata or {}).get("pii_leak_detected"):
                    metrics.pii_leaks_output += 1

            # Secrets
            if entry.event_type == "input_guardrail":
                if (entry.metadata or {}).get("secrets_count", 0) > 0:
                    metrics.secrets_detected += 1

            # Groundedness
            if entry.event_type == "output_guardrail":
                score = (entry.metadata or {}).get("groundedness_score")
                if score is not None:
                    groundedness_scores.append(score)

            # Refusal
            if entry.event_type == "output_guardrail":
                refusal_type = (entry.metadata or {}).get("refusal_type")
                if refusal_type and refusal_type not in ("none", "needs_clarification"):
                    metrics.refusal_count += 1
                if (entry.metadata or {}).get("over_refusal"):
                    metrics.over_refusal_count += 1

            # HITL
            if entry.event_type and entry.event_type.startswith("hitl_"):
                if "submitted" in entry.event_type:
                    pass  # counted in pending below
                elif "approved" in entry.event_type:
                    metrics.hitl_approved += 1
                elif "denied" in entry.event_type:
                    metrics.hitl_denied += 1
                elif "timed_out" in entry.event_type:
                    metrics.hitl_timed_out += 1

            # Circuit breaker
            if entry.event_type == "circuit_breaker":
                metrics.breaker_trips += 1

        # Derived rates
        if metrics.total_interactions > 0:
            metrics.block_rate = round(
                metrics.blocked_interactions / metrics.total_interactions, 3
            )

        if groundedness_scores:
            metrics.groundedness_avg = round(
                sum(groundedness_scores) / len(groundedness_scores), 3
            )
            metrics.groundedness_samples = len(groundedness_scores)

        if metrics.total_interactions > 0:
            metrics.refusal_rate = round(
                metrics.refusal_count / metrics.total_interactions, 3
            )

        return metrics

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> AuditSummary:
        """Quick audit log summary."""
        entries = list(self._logger.read_all())
        report = self._logger.verify_integrity()

        event_types: dict[str, int] = {}
        for entry in entries:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1

        sorted_types = sorted(event_types.items(), key=lambda x: x[1], reverse=True)

        return AuditSummary(
            total_entries=len(entries),
            first_entry_at=entries[0].timestamp if entries else None,
            last_entry_at=entries[-1].timestamp if entries else None,
            integrity_valid=report.valid,
            integrity_errors=len(report.errors),
            unique_event_types=[t[0] for t in sorted_types],
            top_actions=[
                {"event_type": t[0], "count": t[1]}
                for t in sorted_types[:10]
            ],
        )
