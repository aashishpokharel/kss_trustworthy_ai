"""
Input Guardrails Pipeline — orchestrates all input detectors in order.

Architecture (Section 1, Stage 2):
1. InputValidator — normalize unicode, detect homoglyphs, check length
2. InjectionDetector — regex + heuristic + canary
3. PIIDetector — Presidio-based entity recognition + redaction
4. SecretsScanner — regex + entropy-based key/token detection
5. SensitiveTopicClassifier — keyword + pattern classification
6. DataClassifier — assign DataTier based on findings

Order matters: normalization first so obfuscated attacks are decoded.
First blocker stops the pipeline (fail-fast, fail-closed).

Every run produces an InputGuardrailReport logged to the audit log.
"""

from __future__ import annotations

import time

from trust_safety.governance.audit_log.models import AuditEntry
from trust_safety.governance.audit_log.store import AuditLogger
from trust_safety.guardrails.data_classifier import DataClassifier
from trust_safety.guardrails.input.injection_detector import (
    CanaryTokenManager,
    InjectionDetector,
)
from trust_safety.guardrails.input.input_validator import InputValidator
from trust_safety.guardrails.input.models import (
    InjectionResult,
    InputGuardrailReport,
    PIIResult,
    SecretsResult,
    SensitiveTopicResult,
    ValidationResult,
)
from trust_safety.guardrails.input.pii_detector import PIIDetector
from trust_safety.guardrails.input.secrets_scanner import SecretsScanner
from trust_safety.guardrails.input.sensitive_topic_classifier import (
    SensitiveTopicClassifier,
)
from trust_safety.models.base import DataTier
from trust_safety.models.context import ContextBlock


class InputGuardrailPipeline:
    """Execute all input guardrails in order.

    Usage::

        pipeline = InputGuardrailPipeline(audit_logger=logger)
        report = pipeline.run(user_text, context_block)
        if not report.allowed:
            raise BlockedRequest(report)
    """

    def __init__(
        self,
        audit_logger: AuditLogger | None = None,
        injection_strictness: float = 0.1,
        max_input_length: int = 16_000,
    ) -> None:
        self.audit_logger = audit_logger
        self._validator = InputValidator(max_length=max_input_length)
        self._injection_detector = InjectionDetector(strictness=injection_strictness)
        self._pii_detector = PIIDetector()
        self._secrets_scanner = SecretsScanner()
        self._sensitive_classifier = SensitiveTopicClassifier()
        self._data_classifier = DataClassifier()
        self._canary_manager = CanaryTokenManager()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, text: str, context: ContextBlock | None = None) -> InputGuardrailReport:
        """Run all input guardrails against *text*.

        Returns an InputGuardrailReport.  If ``report.allowed`` is False,
        the request must be blocked — check ``report.block_reason`` for why.
        """
        start = time.monotonic()
        detectors_run: list[str] = []
        report = InputGuardrailReport()

        # -- Stage 1: Input validation (normalize + structural checks) --
        detectors_run.append("validation")
        validation = self._validator.validate(text)
        report.validation = validation
        if not validation.valid:
            report.allowed = False
            report.block_reason = "Input validation failed"
            report.detectors_run = detectors_run
            report.total_latency_ms = (time.monotonic() - start) * 1000
            self._audit(report, context)
            return report

        # Use normalized text for all subsequent checks
        safe_text = validation.normalized_text or text

        # -- Stage 2: Injection detection --
        detectors_run.append("injection")
        injection = self._injection_detector.scan(safe_text)
        report.injection = injection
        if injection.is_injection:
            report.allowed = False
            report.block_reason = (
                f"Prompt injection detected: {injection.category} "
                f"(risk={injection.risk_score:.2f})"
            )
            report.detectors_run = detectors_run
            report.total_latency_ms = (time.monotonic() - start) * 1000
            self._audit(report, context)
            return report

        # -- Stage 3: PII detection --
        detectors_run.append("pii")
        pii = self._pii_detector.detect(safe_text)
        report.pii = pii

        # -- Stage 4: Secrets scanning --
        detectors_run.append("secrets")
        secrets = self._secrets_scanner.scan(safe_text)
        report.secrets = secrets
        if secrets.secrets_detected:
            report.allowed = False
            report.block_reason = (
                f"Secrets detected in input: "
                f"{[f.secret_type for f in secrets.findings]}"
            )
            report.detectors_run = detectors_run
            report.total_latency_ms = (time.monotonic() - start) * 1000
            self._audit(report, context)
            return report

        # -- Stage 5: Sensitive topic classification --
        detectors_run.append("sensitive_topics")
        sensitive = self._sensitive_classifier.classify(safe_text)
        report.sensitive_topics = sensitive
        if sensitive.topics_detected and sensitive.strictest_action == "hard_block":
            report.allowed = False
            categories = [f.category for f in sensitive.findings]
            report.block_reason = (
                f"Sensitive topics detected (hard block): {categories}"
            )
            report.detectors_run = detectors_run
            report.total_latency_ms = (time.monotonic() - start) * 1000
            self._audit(report, context)
            return report

        # If crisis content detected, flag but don't block
        if sensitive.topics_detected and sensitive.strictest_action == "safe_response":
            report.block_reason = (
                "Crisis content detected — safe response required"
            )

        # -- Stage 6: Data classification --
        detectors_run.append("data_classifier")
        report.data_tier = self._data_classifier.classify(safe_text, pii, secrets)

        # -- All checks passed --
        report.allowed = True
        report.detectors_run = detectors_run
        report.total_latency_ms = (time.monotonic() - start) * 1000
        self._audit(report, context)
        return report

    # ------------------------------------------------------------------
    # Canary token management
    # ------------------------------------------------------------------

    @property
    def canary_manager(self) -> CanaryTokenManager:
        """Access to the canary token manager for output verification."""
        return self._canary_manager

    def get_canary_instruction(self) -> str:
        """Return the canary-bearing system prompt fragment."""
        return self._canary_manager.generate_canary_instruction()

    def verify_output_canary(self, output_text: str) -> bool:
        """Check if the canary token leaked into model output.

        Returns True if canary was triggered (CRITICAL security event).
        """
        return self._canary_manager.verify_output(output_text)

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    def _audit(
        self, report: InputGuardrailReport, context: ContextBlock | None
    ) -> None:
        """Log the pipeline result to the audit log."""
        if not self.audit_logger:
            return

        entry = AuditEntry(
            event_type="input_guardrail",
            action="input_pipeline_scan",
            user_id=context.provenance.source_id if context and context.provenance else None,
            risk_score=(
                report.injection.risk_score if report.injection else 0.0
            ),
            data_tier=report.data_tier,
            status="blocked" if not report.allowed else "allowed",
            metadata={
                "report_id": report.report_id,
                "allowed": report.allowed,
                "block_reason": report.block_reason,
                "detectors_run": report.detectors_run,
                "injection_category": report.injection.category if report.injection else None,
                "pii_count": len(report.pii.findings) if report.pii else 0,
                "secrets_count": len(report.secrets.findings) if report.secrets else 0,
                "sensitive_topics": (
                    [f.category for f in report.sensitive_topics.findings]
                    if report.sensitive_topics else []
                ),
                "data_tier": report.data_tier.value if report.data_tier else None,
                "latency_ms": report.total_latency_ms,
            },
        )
        self.audit_logger.log(entry)
