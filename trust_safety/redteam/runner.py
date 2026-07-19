"""
Red Team Runner — loads Garak/PyRIT configs and runs probes against endpoints.

The actual Garak/PyRIT tools are external.  This runner provides the
infrastructure to:
1. Load config files (YAML/JSON)
2. Run probes against our API endpoints
3. Collect results into the audit log
4. Report findings with severity + remediation tracking
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.models import AuditEntry
from trust_safety.governance.audit_log.store import AuditLogger


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class ProbeResult(BaseModel):
    """Result of a single probe execution."""
    probe_name: str
    category: str
    payload: str
    blocked: bool
    risk_score: float = 0.0
    response_summary: str = ""
    severity: str = "low"  # low, medium, high, critical


class RedTeamRunReport(BaseModel):
    """Aggregate report from a red-team run."""
    run_id: str = Field(default_factory=lambda: f"rt-{datetime.now(timezone.utc).timestamp():.0f}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_probes: int = 0
    blocked: int = 0
    bypassed: int = 0
    results: list[ProbeResult] = Field(default_factory=list)
    severity_counts: dict[str, int] = Field(default_factory=dict)


# ------------------------------------------------------------------
# RedTeamRunner
# ------------------------------------------------------------------

class RedTeamRunner:
    """Run red-team probes against the trust & safety layer.

    Usage::

        runner = RedTeamRunner(audit_logger=logger)
        report = runner.run_garak_config("redteam/garak_configs/default.yaml")
        # Results are in report AND audit log
    """

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self.audit_logger = audit_logger

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def load_garak_config(self, path: str | Path) -> dict[str, Any]:
        """Load a Garak YAML config file."""
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_pyrit_config(self, path: str | Path) -> dict[str, Any]:
        """Load a PyRIT JSON config file."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Probe execution
    # ------------------------------------------------------------------

    def run_probes(
        self,
        probes: list[dict[str, Any]],
        target_endpoint: str = "/api/v1/guardrails/input/scan",
    ) -> RedTeamRunReport:
        """Execute *probes* against *target_endpoint*.

        Each probe is a dict with at minimum: ``{"name": str, "payload": str}``.
        """
        report = RedTeamRunReport()
        report.total_probes = len(probes)

        for probe_def in probes:
            result = self._execute_single_probe(probe_def, target_endpoint)
            report.results.append(result)

            if result.blocked:
                report.blocked += 1
            else:
                report.bypassed += 1

            report.severity_counts[result.severity] = (
                report.severity_counts.get(result.severity, 0) + 1
            )

            # Log to audit
            self._audit_finding(result)

        return report

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _execute_single_probe(
        self, probe_def: dict[str, Any], endpoint: str
    ) -> ProbeResult:
        """Execute a single probe against the API.

        In production, this would make an HTTP call to the endpoint.
        Here we run the payload through the injection detector directly.
        """
        from trust_safety.guardrails.input.injection_detector import InjectionDetector

        detector = InjectionDetector(strictness=0.1)
        result = detector.scan(probe_def.get("payload", ""))

        return ProbeResult(
            probe_name=probe_def.get("name", "unnamed"),
            category=probe_def.get("category", "unknown"),
            payload=probe_def.get("payload", "")[:200],
            blocked=result.is_injection,
            risk_score=result.risk_score,
            response_summary=f"Category: {result.category}, Patterns: {len(result.matched_patterns)}",
            severity=self._severity_from_score(result.risk_score),
        )

    def _audit_finding(self, result: ProbeResult) -> None:
        """Log a red-team finding to the audit log."""
        if not self.audit_logger:
            return

        entry = AuditEntry(
            event_type="red_team_finding",
            action=f"Red-team probe: {result.probe_name}",
            risk_score=result.risk_score,
            status="blocked" if result.blocked else "allowed",
            metadata={
                "probe_name": result.probe_name,
                "category": result.category,
                "severity": result.severity,
                "bypassed": not result.blocked,
            },
        )
        self.audit_logger.log(entry)

    @staticmethod
    def _severity_from_score(score: float) -> str:
        if score >= 0.7:
            return "critical"
        if score >= 0.4:
            return "high"
        if score >= 0.15:
            return "medium"
        return "low"
