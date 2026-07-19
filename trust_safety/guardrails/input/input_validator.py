"""
Input Validator — Unicode normalization, homoglyph detection,
length limits, encoding checks (Section 7).

Runs FIRST in the pipeline so obfuscated attacks are decoded before
reaching pattern-based classifiers.

Fail-closed: any issue that isn't explicitly advisory blocks the request.
"""

from __future__ import annotations

import unicodedata
from typing import ClassVar

from trust_safety.guardrails.input.models import ValidationFinding, ValidationResult

# ------------------------------------------------------------------
# Homoglyph / confusable character table
# ------------------------------------------------------------------

# Map of confusable Unicode characters → the ASCII they impersonate.
# This is a curated subset of the full Unicode confusables table.
# Characters that are visually identical or near-identical to ASCII.

HOMOGLYPH_MAP: dict[int, str] = {
    # Cyrillic → Latin (most common injection vector)
    0x0430: "a",  # Cyrillic а → Latin a
    0x0435: "e",  # Cyrillic е → Latin e
    0x043E: "o",  # Cyrillic о → Latin o
    0x0440: "p",  # Cyrillic р → Latin p
    0x0441: "c",  # Cyrillic с → Latin c
    0x0443: "y",  # Cyrillic у → Latin y
    0x0445: "x",  # Cyrillic х → Latin x
    0x0410: "A",  # Cyrillic А → Latin A
    0x0415: "E",  # Cyrillic Е → Latin E
    0x041E: "O",  # Cyrillic О → Latin O
    0x0420: "P",  # Cyrillic Р → Latin P
    0x0421: "C",  # Cyrillic С → Latin C
    0x0425: "X",  # Cyrillic Х → Latin X
    0x0422: "T",  # Cyrillic Т → Latin T
    0x041D: "H",  # Cyrillic Н → Latin H
    0x041C: "M",  # Cyrillic М → Latin M
    0x041A: "K",  # Cyrillic К → Latin K
    0x0412: "B",  # Cyrillic В → Latin B
    # Greek → Latin
    0x03BF: "o",  # Greek ο → Latin o
    0x03C1: "p",  # Greek ρ → Latin p
    0x039F: "O",  # Greek Ο → Latin O
    0x03A1: "P",  # Greek Ρ → Latin P
}

# Zero-width and invisible characters often used in obfuscation
ZERO_WIDTH_CHARS: set[int] = {
    0x200B,  # Zero-width space
    0x200C,  # Zero-width non-joiner
    0x200D,  # Zero-width joiner
    0xFEFF,  # BOM / zero-width no-break space
    0x2060,  # Word joiner
    0x2061,  # Function application
    0x2062,  # Invisible times
    0x2063,  # Invisible separator
    0x2064,  # Invisible plus
}


# ------------------------------------------------------------------
# InputValidator
# ------------------------------------------------------------------

class InputValidator:
    """Pre-processing validation for all input text.

    Runs before any other classifier.  Normalizes unicode, detects
    homoglyph attacks, checks length limits, and validates encoding.

    Usage::

        validator = InputValidator(max_length=8000)
        result = validator.validate(user_input)
        if not result.valid:
            raise BlockedRequest(result)
        safe_text = result.normalized_text
    """

    MAX_LENGTH_DEFAULT = 16_000
    MIN_LENGTH = 1

    def __init__(self, max_length: int = MAX_LENGTH_DEFAULT) -> None:
        self.max_length = max_length

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def validate(self, text: str) -> ValidationResult:
        """Validate and normalize *text*.

        Returns a ValidationResult.  If ``valid=False`` the input is
        blocked.  ``normalized_text`` is the NFKC-normalized version.
        """
        findings: list[ValidationFinding] = []

        # 1. Empty check
        if not text or not text.strip():
            findings.append(ValidationFinding(
                issue_type="empty_input",
                detail="Input is empty or whitespace-only.",
                blocked=True,
            ))
            return ValidationResult(valid=False, findings=findings)

        # 2. Length check
        length_finding = self._check_length(text)
        if length_finding:
            findings.append(length_finding)
            # Length violation is a hard block
            return ValidationResult(valid=False, findings=findings)

        # 3. Encoding / control character check
        encoding_findings = self._check_encoding(text)
        findings.extend(encoding_findings)
        if any(f.blocked for f in encoding_findings):
            return ValidationResult(valid=False, findings=findings)

        # 4. Homoglyph / confusable detection
        homoglyph_finding = self._check_homoglyphs(text)
        if homoglyph_finding:
            findings.append(homoglyph_finding)
            # Homoglyphs are a hard block
            return ValidationResult(valid=False, findings=findings)

        # 5. Unicode normalization (NFKC)
        normalized = unicodedata.normalize("NFKC", text)

        return ValidationResult(
            valid=True,
            normalized_text=normalized,
            findings=findings,
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_length(self, text: str) -> ValidationFinding | None:
        """Check text length against configured limits."""
        if len(text) > self.max_length:
            return ValidationFinding(
                issue_type="length_exceeded",
                detail=f"Input length {len(text)} exceeds maximum {self.max_length}.",
                blocked=True,
            )
        if len(text.strip()) < self.MIN_LENGTH:
            return ValidationFinding(
                issue_type="too_short",
                detail=f"Input too short ({len(text)} chars).",
                blocked=True,
            )
        return None

    def _check_encoding(self, text: str) -> list[ValidationFinding]:
        """Check for encoding issues and hidden characters."""
        findings: list[ValidationFinding] = []

        # Detect zero-width characters
        zw_count = sum(1 for c in text if ord(c) in ZERO_WIDTH_CHARS)
        if zw_count > 3:
            findings.append(ValidationFinding(
                issue_type="zero_width_chars",
                detail=f"Found {zw_count} zero-width/invisible characters — "
                       f"possible obfuscation attempt.",
                blocked=True,
            ))

        # Detect excessive control characters
        control_count = sum(
            1 for c in text
            if ord(c) < 32 and ord(c) not in {9, 10, 13}  # tab, LF, CR OK
        )
        if control_count > 5:
            findings.append(ValidationFinding(
                issue_type="control_characters",
                detail=f"Found {control_count} control characters — "
                       f"possible encoding trick.",
                blocked=True,
            ))

        return findings

    def _check_homoglyphs(self, text: str) -> ValidationFinding | None:
        """Detect confusable/homoglyph characters used for obfuscation.

        An attacker might replace Latin 'a' with Cyrillic 'а' (U+0430)
        to bypass keyword filters.  We flag any mix of scripts that
        includes confusable characters.
        """
        homoglyphs_found: list[str] = []

        for char in text:
            cp = ord(char)
            if cp in HOMOGLYPH_MAP:
                homoglyphs_found.append(
                    f"U+{cp:04X}→'{HOMOGLYPH_MAP[cp]}'"
                )

        if homoglyphs_found:
            unique = list(set(homoglyphs_found))
            return ValidationFinding(
                issue_type="homoglyph_detected",
                detail=(
                    f"Found {len(homoglyphs_found)} confusable character(s): "
                    f"{', '.join(unique[:5])}.  "
                    f"This may be an obfuscation attempt."
                ),
                blocked=True,
            )

        return None
