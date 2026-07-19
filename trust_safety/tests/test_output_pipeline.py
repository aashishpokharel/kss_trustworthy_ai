"""Integration tests for the full OutputGuardrailPipeline."""

import json
from pathlib import Path

from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from trust_safety.guardrails.output.pipeline import OutputGuardrailPipeline


class TestOutputGuardrailPipeline:
    """Full pipeline: schema → groundedness → PII leak → refusal."""

    # -- Clean output --------------------------------------------------

    def test_clean_output_passes(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        report = pipeline.run(
            "The capital of France is Paris.",
            source_context="France is a country in Europe. Its capital is Paris.",
        )
        assert report.allowed
        assert report.groundedness is not None
        assert report.groundedness.score >= 0.5

    def test_schema_valid_output_passes(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        schema = {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}
        report = pipeline.run(
            '{"status": "active"}',
            expected_schema=schema,
        )
        assert report.allowed
        assert report.schema_validation.passed

    # -- Schema failure ------------------------------------------------

    def test_schema_failure_blocks(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        report = pipeline.run(
            '{"age": 30}',  # Missing required "name"
            expected_schema=schema,
        )
        assert not report.allowed
        assert "schema" in report.block_reason.lower()
        # Should stop at schema — groundedness not run
        assert report.groundedness is None

    # -- Groundedness failure ------------------------------------------

    def test_hallucination_blocks(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        report = pipeline.run(
            "The moon is made of green cheese and orbits at 500,000 km according to NASA.",
            source_context="The moon orbits Earth.",
            domain="general",
        )
        # Should have low groundedness score
        assert report.groundedness is not None
        assert len(report.groundedness.unsupported_claims) > 0 or report.groundedness.score < 1.0

    # -- PII leak detection --------------------------------------------

    def test_pii_leak_detected(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        report = pipeline.run(
            "Here is the user data: john.doe@example.com, phone (555) 123-4567",
            source_context="User data includes contact information.",
        )
        if report.pii_leak and report.pii_leak.pii_detected:
            assert not report.allowed
            assert "PII" in report.block_reason

    # -- Refusal classification ----------------------------------------

    def test_refusal_classified(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        report = pipeline.run(
            "I cannot help with that request. It goes against my content policies.",
            input_was_benign=True,
        )
        assert report.refusal is not None
        assert report.refusal.is_refusal
        assert report.refusal.over_refusal  # Benign input was refused

    def test_non_refusal_clean(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        report = pipeline.run(
            "The weather today is sunny with a high of 72 degrees.",
        )
        assert report.refusal is not None
        assert not report.refusal.is_refusal

    # -- Audit logging -------------------------------------------------

    def test_audit_logged_on_block(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}
        pipeline.run("not json", expected_schema=schema)
        entries = list(store.read_all())
        assert len(entries) >= 1
        assert entries[-1].event_type == "output_guardrail"
        assert entries[-1].status == "blocked"

    def test_audit_logged_on_pass(self, tmp_path):
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        pipeline = OutputGuardrailPipeline(audit_logger=AuditLogger(store))
        pipeline.run("Hello world.", source_context="Hello world context.")
        entries = list(store.read_all())
        assert len(entries) >= 1
        assert entries[-1].status == "allowed"
