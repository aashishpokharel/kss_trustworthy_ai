"""Tests for IncidentTracker — incident lifecycle and golden set feedback."""

from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from trust_safety.governance.incident_review import (
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    IncidentTracker,
)


class TestIncidentTracker:
    """Incident lifecycle: report → investigate → resolve."""

    def test_report_creates_open_incident(self):
        tracker = IncidentTracker()
        incident = tracker.report(
            "Injection bypass via encoding",
            severity=IncidentSeverity.HIGH,
            source=IncidentSource.RED_TEAM,
        )
        assert incident.status == IncidentStatus.OPEN
        assert incident.severity == IncidentSeverity.HIGH

    def test_investigate_adds_findings(self):
        tracker = IncidentTracker()
        incident = tracker.report("Test incident")
        updated = tracker.investigate(incident.incident_id, ["Root cause: missing pattern"])
        assert updated.status == IncidentStatus.INVESTIGATING
        assert "Root cause: missing pattern" in updated.findings

    def test_resolve_closes_incident(self):
        tracker = IncidentTracker()
        incident = tracker.report("Bug in detector")
        tracker.resolve(
            incident.incident_id,
            remediation="Added new patterns to injection detector",
            golden_set_updates=["Added encoding bypass payload to golden set"],
        )
        resolved = tracker.get(incident.incident_id)
        assert resolved.status == IncidentStatus.RESOLVED
        assert resolved.golden_set_updates == ["Added encoding bypass payload to golden set"]

    def test_wont_fix(self):
        tracker = IncidentTracker()
        incident = tracker.report("Low-priority cosmetic issue", severity=IncidentSeverity.LOW)
        tracker.wont_fix(incident.incident_id, "Not exploitable")
        updated = tracker.get(incident.incident_id)
        assert updated.status == IncidentStatus.WONT_FIX

    def test_list_open(self):
        tracker = IncidentTracker()
        tracker.report("Issue A")
        tracker.report("Issue B")
        inc3 = tracker.report("Issue C")
        tracker.resolve(inc3.incident_id, "Fixed")
        assert len(tracker.list_open()) == 2

    def test_get_trends(self):
        tracker = IncidentTracker()
        tracker.report("Low", severity=IncidentSeverity.LOW)
        tracker.report("High", severity=IncidentSeverity.HIGH)
        tracker.report("Critical", severity=IncidentSeverity.CRITICAL)
        trends = tracker.get_trends()
        assert trends["low"] == 1
        assert trends["high"] == 1
        assert trends["critical"] == 1

    def test_audit_logged(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        tracker = IncidentTracker(audit_logger=logger)
        tracker.report("Test incident")
        entries = list(store.read_all())
        assert len(entries) >= 1
        assert entries[-1].event_type == "incident_reported"

    def test_nonexistent_raises(self):
        tracker = IncidentTracker()
        try:
            tracker.investigate("nonexistent", ["finding"])
            assert False, "Should have raised"
        except ValueError:
            pass
