"""
Incident Review Loop — structured incident tracking with golden set feedback (Section 13).

Every guardrail block, HITL escalation, and red-team finding can become an
incident.  Resolved incidents feed new test cases back into eval suites,
closing the loop from detection → investigation → fix → regression test.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.store import AuditLogger


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


class IncidentSource(str, Enum):
    RED_TEAM = "red_team"
    USER_REPORT = "user_report"
    AUTO_DETECTION = "auto_detection"
    HITL_ESCALATION = "hitl_escalation"


class Incident(BaseModel):
    """A tracked security/safety incident."""
    incident_id: str = Field(
        default_factory=lambda: (
            f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            f"-{__import__('os').urandom(3).hex()}"
        )
    )
    title: str
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    source: IncidentSource = IncidentSource.AUTO_DETECTION
    status: IncidentStatus = IncidentStatus.OPEN
    findings: list[str] = Field(default_factory=list)
    remediation: str = ""
    golden_set_updates: list[str] = Field(default_factory=list)
    reported_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentTracker:
    """Track and manage security/safety incidents.

    Usage::

        tracker = IncidentTracker(audit_logger=logger)
        incident = tracker.report(
            "Injection bypass via encoding trick",
            severity=IncidentSeverity.HIGH,
            source=IncidentSource.RED_TEAM,
        )
        tracker.resolve(incident.incident_id, "Added encoding patterns to detector")
    """

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._incidents: dict[str, Incident] = {}
        self.audit_logger = audit_logger

    # -- Reporting ----------------------------------------------------

    def report(
        self,
        title: str,
        description: str = "",
        severity: IncidentSeverity = IncidentSeverity.MEDIUM,
        source: IncidentSource = IncidentSource.AUTO_DETECTION,
        reported_by: str = "system",
    ) -> Incident:
        incident = Incident(
            title=title, description=description,
            severity=severity, source=source, reported_by=reported_by,
        )
        self._incidents[incident.incident_id] = incident
        self._audit("incident_reported", incident)
        return incident

    # -- Investigation ------------------------------------------------

    def investigate(self, incident_id: str, findings: list[str]) -> Incident:
        incident = self._get(incident_id)
        incident.status = IncidentStatus.INVESTIGATING
        incident.findings = findings
        self._audit("incident_investigating", incident)
        return incident

    # -- Resolution ---------------------------------------------------

    def resolve(
        self,
        incident_id: str,
        remediation: str = "",
        golden_set_updates: list[str] | None = None,
    ) -> Incident:
        incident = self._get(incident_id)
        incident.status = IncidentStatus.RESOLVED
        incident.remediation = remediation
        incident.golden_set_updates = golden_set_updates or []
        incident.resolved_at = datetime.now(timezone.utc)
        self._audit("incident_resolved", incident)
        return incident

    def wont_fix(self, incident_id: str, reason: str = "") -> Incident:
        incident = self._get(incident_id)
        incident.status = IncidentStatus.WONT_FIX
        incident.remediation = reason
        incident.resolved_at = datetime.now(timezone.utc)
        self._audit("incident_wont_fix", incident)
        return incident

    # -- Query --------------------------------------------------------

    def list_open(self) -> list[Incident]:
        return [
            i for i in self._incidents.values()
            if i.status in (IncidentStatus.OPEN, IncidentStatus.INVESTIGATING)
        ]

    def list_all(self) -> list[Incident]:
        return list(self._incidents.values())

    def get_trends(self) -> dict[str, int]:
        """Incident counts by severity."""
        counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for incident in self._incidents.values():
            counts[incident.severity.value] = counts.get(incident.severity.value, 0) + 1
        return counts

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    # -- Internal -----------------------------------------------------

    def _get(self, incident_id: str) -> Incident:
        if incident_id not in self._incidents:
            raise ValueError(f"Incident '{incident_id}' not found")
        return self._incidents[incident_id]

    def _audit(self, event: str, incident: Incident) -> None:
        if not self.audit_logger:
            return
        from trust_safety.governance.audit_log.models import AuditEntry
        entry = AuditEntry(
            event_type=event,
            action=f"Incident: {incident.title}",
            risk_score={"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}.get(
                incident.severity.value, 0.5
            ),
            status=incident.status.value,
            metadata={
                "incident_id": incident.incident_id,
                "severity": incident.severity.value,
                "source": incident.source.value,
                "findings": incident.findings,
                "remediation": incident.remediation,
            },
        )
        self.audit_logger.log(entry)
