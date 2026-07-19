"""
Output Guardrails Pipeline — orchestrates output-side detectors in order.

Architecture (Section 1, Stage 5):
1. Schema validation — structural conformance
2. Groundedness — factual accuracy against source context
3. PII leak check — reuse Phase 1 PIIDetector on output
4. Refusal classification — categorize refusal type

Order: schema first (structural), then groundedness (factual), then
PII leak (privacy), then refusal (intent).  Schema failure stops the
pipeline — don't bother checking groundedness of malformed output.
"""

from __future__ import annotations

import time
from typing import Any

from trust_safety.governance.audit_log.models import AuditEntry
from trust_safety.governance.audit_log.store import AuditLogger
from trust_safety.guardrails.input.pii_detector import PIIDetector
from trust_safety.guardrails.output.groundedness_checker import (
    DomainType,
    GroundednessChecker,
)
from trust_safety.guardrails.output.models import (
    OutputGuardrailReport,
)
from trust_safety.guardrails.output.refusal_classifier import RefusalClassifier
from trust_safety.guardrails.output.schema_validator import OutputSchemaValidator
from trust_safety.models.context import ContextBlock


class OutputGuardrailPipeline:
    """Execute all output guardrails in order.

    Usage::

        pipeline = OutputGuardrailPipeline(audit_logger=logger)
        report = pipeline.run(
            output_text='{"name": "John"}',
            source_context="The user's name is John.",
            expected_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        )
        if not report.allowed:
            # Feed report.schema_validation.retry_prompt back to LLM
    """

    def __init__(
        self,
        audit_logger: AuditLogger | None = None,
        default_domain: DomainType = "general",
    ) -> None:
        self.audit_logger = audit_logger
        self.default_domain = default_domain
        self._schema_validator = OutputSchemaValidator()
        self._groundedness_checker = GroundednessChecker()
        self._pii_detector = PIIDetector()
        self._refusal_classifier = RefusalClassifier()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(
        self,
        output_text: str,
        source_context: str | None = None,
        expected_schema: dict[str, Any] | None = None,
        domain: DomainType = "general",
        input_was_benign: bool = True,
        context: ContextBlock | None = None,
    ) -> OutputGuardrailReport:
        """Run all output guardrails against *output_text*.

        Args:
            output_text: The LLM's output to validate.
            source_context: Grounding context (RAG chunks, etc.).
            expected_schema: Optional JSON Schema for structured output.
            domain: Domain for groundedness thresholds.
            input_was_benign: Was the input known-benign? (For over-refusal check).
            context: Optional ContextBlock for audit log provenance.
        """
        start = time.monotonic()
        detectors_run: list[str] = []
        report = OutputGuardrailReport()

        # -- Stage 1: Schema validation --
        if expected_schema:
            detectors_run.append("schema_validation")
            schema_result = self._schema_validator.validate(
                output_text, expected_schema
            )
            report.schema_validation = schema_result
            if not schema_result.passed:
                report.allowed = False
                report.block_reason = f"Schema validation failed: {'; '.join(schema_result.errors[:3])}"
                report.detectors_run = detectors_run
                report.total_latency_ms = (time.monotonic() - start) * 1000
                self._audit(report, context)
                return report

        # -- Stage 2: Groundedness / hallucination check --
        detectors_run.append("groundedness")
        groundedness = self._groundedness_checker.check(
            output_text, source_context, domain
        )
        report.groundedness = groundedness
        if not groundedness.passed and domain != "creative":
            report.allowed = False
            report.block_reason = (
                f"Groundedness check failed: score={groundedness.score:.2f} "
                f"below threshold={groundedness.domain_threshold:.2f} "
                f"({len(groundedness.unsupported_claims)} unsupported claims)"
            )
            report.detectors_run = detectors_run
            report.total_latency_ms = (time.monotonic() - start) * 1000
            self._audit(report, context)
            return report

        # -- Stage 3: PII leak check (output side) --
        detectors_run.append("pii_leak")
        pii_result = self._pii_detector.detect(output_text)
        report.pii_leak = pii_result
        if pii_result.pii_detected:
            report.allowed = False
            report.block_reason = (
                f"PII leak detected in output: "
                f"{[f.entity_type for f in pii_result.findings]}"
            )
            report.detectors_run = detectors_run
            report.total_latency_ms = (time.monotonic() - start) * 1000
            self._audit(report, context)
            return report

        # -- Stage 4: Refusal classification --
        detectors_run.append("refusal")
        refusal = self._refusal_classifier.check_over_refusal(
            output_text, was_input_benign=input_was_benign
        )
        report.refusal = refusal
        if refusal.over_refusal:
            # Over-refusal doesn't block but is flagged for review
            report.block_reason = (
                f"Over-refusal detected: legitimate request was refused "
                f"({refusal.refusal_type})"
            )

        # -- All checks passed --
        report.allowed = True
        report.detectors_run = detectors_run
        report.total_latency_ms = (time.monotonic() - start) * 1000
        self._audit(report, context)
        return report

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    def _audit(
        self, report: OutputGuardrailReport, context: ContextBlock | None
    ) -> None:
        """Log the pipeline result to the audit log."""
        if not self.audit_logger:
            return

        entry = AuditEntry(
            event_type="output_guardrail",
            action="output_pipeline_scan",
            user_id=context.provenance.source_id if context and context.provenance else None,
            risk_score=(
                1.0 - report.groundedness.score
                if report.groundedness else 0.0
            ),
            status="blocked" if not report.allowed else "allowed",
            metadata={
                "report_id": report.report_id,
                "allowed": report.allowed,
                "block_reason": report.block_reason,
                "detectors_run": report.detectors_run,
                "schema_passed": report.schema_validation.passed if report.schema_validation else None,
                "groundedness_score": report.groundedness.score if report.groundedness else None,
                "unsupported_claims": report.groundedness.unsupported_claims if report.groundedness else [],
                "pii_leak_detected": report.pii_leak.pii_detected if report.pii_leak else False,
                "refusal_type": report.refusal.refusal_type if report.refusal else None,
                "over_refusal": report.refusal.over_refusal if report.refusal else False,
                "latency_ms": report.total_latency_ms,
            },
        )
        self.audit_logger.log(entry)
