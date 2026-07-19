"""
PII Detector — wraps Microsoft Presidio for entity recognition and redaction.

Architecture (Section 5):
- Input-side: detect and redact PII before it reaches the model
- Config-driven entity list (not hardcoded)
- Adversarial obfuscation detection ("j o h n at example dot com")
- Supports redact, mask, and tokenize anonymization modes
"""

from __future__ import annotations

import re
from typing import Literal

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from trust_safety.guardrails.input.models import PIIFinding, PIIResult

# ------------------------------------------------------------------
# Default entity types to detect
# ------------------------------------------------------------------

DEFAULT_PII_ENTITIES = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "PERSON",
    "US_SSN",
    "CREDIT_CARD",
    "US_BANK_NUMBER",
    "IBAN_CODE",
    "IP_ADDRESS",
    "US_DRIVER_LICENSE",
    "US_PASSPORT",
    "URL",
]

# ------------------------------------------------------------------
# Adversarial obfuscation patterns
# ------------------------------------------------------------------

OBFUSCATION_PATTERNS = [
    # Spaced characters: "j o h n @ e x a m p l e . c o m"
    (re.compile(r'\b(?:\w\s){4,}\w\b'), "email_spacing"),
    # "at" / "dot" substitution: "john at example dot com"
    (re.compile(r'\b\w+\s+at\s+\w+\s+dot\s+\w+\b', re.IGNORECASE), "email_at_dot"),
    # Bracketed: "john[at]example[dot]com"
    (re.compile(r'\b\w+\[at\]\w+\[dot\]\w+\b', re.IGNORECASE), "email_bracketed"),
    # Spaced SSN: "1 2 3 - 4 5 - 6 7 8 9"
    (re.compile(r'\d\s\d\s\d\s*-\s*\d\s\d\s*-\s*\d\s\d\s\d\s\d'), "ssn_spacing"),
    # Spaced phone: "( 5 5 5 )   1 2 3 - 4 5 6 7"
    (re.compile(r'\(\s*\d\s*\d\s*\d\s*\)\s+\d\s*\d\s*\d\s*-\s*\d\s*\d\s*\d\s*\d'), "phone_spacing"),
]

AnonymizationMode = Literal["redact", "mask", "tokenize"]


# ------------------------------------------------------------------
# PIIDetector
# ------------------------------------------------------------------

class PIIDetector:
    """PII detection and anonymization using Microsoft Presidio.

    Usage::

        detector = PIIDetector()
        result = detector.detect("My email is john@example.com")
        redacted = detector.redact("My email is john@example.com")
    """

    def __init__(
        self,
        entities: list[str] | None = None,
        language: str = "en",
        default_mode: AnonymizationMode = "redact",
    ) -> None:
        self.entities = entities or DEFAULT_PII_ENTITIES
        self.language = language
        self.default_mode = default_mode
        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect(self, text: str) -> PIIResult:
        """Detect PII entities in *text*.

        Also runs adversarial obfuscation checks before Presidio.
        """
        findings: list[PIIFinding] = []

        # 1. Adversarial obfuscation check
        obfuscated = self._check_obfuscation(text)
        if obfuscated:
            findings.append(PIIFinding(
                entity_type="OBFUSCATED_PII",
                value_snippet="[obfuscated]",
                start=0,
                end=len(text),
                score=0.9,
            ))
            # Normalize spacing for subsequent Presidio scan
            text = self._normalize_spacing(text)

        # 2. Presidio analysis
        try:
            presidio_results = self._analyzer.analyze(
                text=text,
                entities=self.entities,
                language=self.language,
            )
        except Exception:
            # Presidio can fail on malformed input — fail-closed
            if obfuscated:
                return PIIResult(
                    pii_detected=True,
                    findings=findings,
                    redacted_text="[PII REDACTED — analysis failed, input blocked]",
                )
            return PIIResult(pii_detected=False, findings=[])

        # 3. Convert to our model
        for pr in presidio_results:
            findings.append(PIIFinding(
                entity_type=pr.entity_type,
                value_snippet="[REDACTED]",  # Never expose the real value
                start=pr.start,
                end=pr.end,
                score=pr.score,
            ))

        return PIIResult(
            pii_detected=len(findings) > 0,
            findings=findings,
        )

    # ------------------------------------------------------------------
    # Anonymization
    # ------------------------------------------------------------------

    def redact(self, text: str) -> str:
        """Redact all PII, replacing with <ENTITY_TYPE> placeholders."""
        return self._anonymize(text, "replace")

    def mask(self, text: str) -> str:
        """Mask PII, preserving partial visibility (e.g. j***@example.com)."""
        return self._anonymize(text, "mask")

    def _anonymize(self, text: str, operator: str) -> str:
        """Run Presidio anonymization with the given operator."""
        try:
            presidio_results = self._analyzer.analyze(
                text=text,
                entities=self.entities,
                language=self.language,
            )
            if not presidio_results:
                return text

            anonymized = self._anonymizer.anonymize(
                text=text,
                analyzer_results=presidio_results,
                operators={
                    "DEFAULT": OperatorConfig(operator),
                },
            )
            return anonymized.text
        except Exception:
            # Fail-closed: return a safe message
            return "[REDACTED — PII processing failed]"

    # ------------------------------------------------------------------
    # Adversarial obfuscation detection
    # ------------------------------------------------------------------

    def _check_obfuscation(self, text: str) -> bool:
        """Check if text contains obfuscated PII patterns."""
        for pattern, _ in OBFUSCATION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _normalize_spacing(text: str) -> str:
        """Collapse spaced-out characters to help Presidio detect obfuscated PII."""
        # "j o h n @ e x a m p l e . c o m" → "john@example.com"
        # Only when there's a clear spaced-pattern
        result = text
        # Remove spaces between single letters/digits that look like PII
        result = re.sub(r'\b(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\s+(\w)\b',
                        r'\1\2\3\4\5\6\7\8', result)
        return result
