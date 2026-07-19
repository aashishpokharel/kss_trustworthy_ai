"""Tests for MetricsCollector — governance dashboard metrics."""

from trust_safety.governance.audit_log.models import AuditEntry
from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from trust_safety.governance.dashboard import MetricsCollector


class TestDashboard:
    """Governance dashboard metrics from audit log."""

    def test_empty_log(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        collector = MetricsCollector(logger)
        metrics = collector.get_metrics(hours=24)
        assert metrics.total_interactions == 0
        assert metrics.block_rate == 0.0

    def test_get_summary(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        # Seed some entries
        logger.log(AuditEntry(event_type="llm_call", action="test 1", status="allowed"))
        logger.log(AuditEntry(event_type="input_guardrail", action="test 2", status="blocked"))
        logger.log(AuditEntry(event_type="output_guardrail", action="test 3", status="allowed"))

        collector = MetricsCollector(logger)
        summary = collector.get_summary()
        assert summary.total_entries == 3
        assert summary.integrity_valid

    def test_metrics_counts_blocks(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        logger.log(AuditEntry(event_type="llm_call", action="ok", status="allowed"))
        logger.log(AuditEntry(event_type="input_guardrail", action="blocked",
                              status="blocked", metadata={"injection_category": "direct_injection"}))
        logger.log(AuditEntry(event_type="input_guardrail", action="blocked2",
                              status="blocked", metadata={"secrets_count": 1}))

        collector = MetricsCollector(logger)
        metrics = collector.get_metrics(hours=24)
        assert metrics.total_interactions == 3
        assert metrics.blocked_interactions == 2
        assert metrics.injection_attempts == 1
        assert metrics.secrets_detected == 1

    def test_metrics_groundedness(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        logger.log(AuditEntry(event_type="output_guardrail", action="g1",
                              status="allowed", metadata={"groundedness_score": 0.9}))
        logger.log(AuditEntry(event_type="output_guardrail", action="g2",
                              status="allowed", metadata={"groundedness_score": 0.5}))

        collector = MetricsCollector(logger)
        metrics = collector.get_metrics(hours=24)
        assert metrics.groundedness_avg == 0.7
        assert metrics.groundedness_samples == 2

    def test_metrics_refusal_rate(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        logger.log(AuditEntry(event_type="output_guardrail", action="refusal",
                              status="allowed", metadata={"refusal_type": "policy_violation"}))
        logger.log(AuditEntry(event_type="output_guardrail", action="normal",
                              status="allowed", metadata={"refusal_type": "none"}))
        logger.log(AuditEntry(event_type="output_guardrail", action="normal2",
                              status="allowed", metadata={"refusal_type": "none"}))

        collector = MetricsCollector(logger)
        metrics = collector.get_metrics(hours=24)
        assert metrics.refusal_count == 1
        assert metrics.refusal_rate == pytest.approx(0.333, abs=0.01)

    def test_metrics_over_refusal(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        logger.log(AuditEntry(event_type="output_guardrail", action="over",
                              status="allowed", metadata={"over_refusal": True}))

        collector = MetricsCollector(logger)
        metrics = collector.get_metrics(hours=24)
        assert metrics.over_refusal_count == 1

    def test_metrics_circuit_breaker_trips(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        logger.log(AuditEntry(event_type="circuit_breaker", action="tripped",
                              status="blocked"))

        collector = MetricsCollector(logger)
        metrics = collector.get_metrics(hours=24)
        assert metrics.breaker_trips == 1

    def test_summary_event_types(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        logger.log(AuditEntry(event_type="llm_call", action="a", status="allowed"))
        logger.log(AuditEntry(event_type="input_guardrail", action="b", status="blocked"))

        collector = MetricsCollector(logger)
        summary = collector.get_summary()
        assert "llm_call" in summary.unique_event_types
        assert "input_guardrail" in summary.unique_event_types


import pytest  # noqa: E402
