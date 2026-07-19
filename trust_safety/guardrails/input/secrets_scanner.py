"""
Secrets Scanner — detect API keys, tokens, passwords in input (Section 6).

Two-layer detection:
1. Regex patterns for known key formats (AWS, GitHub, OpenAI, etc.)
2. Entropy-based detection for high-entropy substrings (catch unknown formats)

Never logs the actual secret value — only redacted snippets.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from trust_safety.guardrails.input.models import SecretFinding, SecretsResult

# ------------------------------------------------------------------
# Known secret patterns
# ------------------------------------------------------------------

SECRET_PATTERNS: dict[str, str] = {
    "aws_access_key": r'\bAKIA[0-9A-Z]{16}\b',
    "aws_secret_key": r'\baws[_-]?secret[_-]?(?:key|token|access)[=:]\s*[A-Za-z0-9+/]{20,}',
    "github_token": r'\bgh[pousr]_[A-Za-z0-9_]{36,255}\b',
    "openai_api_key": r'\bsk-(?:proj-)?[A-Za-z0-9]{32,}\b',
    "anthropic_api_key": r'\bsk-ant-[A-Za-z0-9]{32,}\b',
    "google_api_key": r'\bAIza[0-9A-Za-z_-]{35}\b',
    "jwt_token": r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
    "generic_api_key": r'(?i)\b(?:api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*[A-Za-z0-9_-]{16,}',
    "private_key_header": r'-----BEGIN\s+(RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----',
    "connection_string": r'(?:mongodb|postgresql|mysql|redis|sqlite)://[^ ]+:[^ @]+@',
    "slack_token": r'\bxox[bpsar]-[A-Za-z0-9-]+',
    "password_in_code": r'(?i)(?:password|passwd|pwd|secret)\s*[=:]\s*[\"\'][^\"\']{4,}[\"\']',
    "discord_token": r'[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}',
}


# ------------------------------------------------------------------
# Entropy calculation
# ------------------------------------------------------------------

def _shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy of *data* (bits per character)."""
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


# ------------------------------------------------------------------
# SecretsScanner
# ------------------------------------------------------------------

class SecretsScanner:
    """Detect secrets (API keys, tokens, passwords) in text.

    Usage::

        scanner = SecretsScanner()
        result = scanner.scan(user_input)
        if result.secrets_detected:
            safe_text = result.redacted_text
    """

    # Entropy threshold: substrings with entropy above this are suspicious
    ENTROPY_THRESHOLD = 4.0
    # Minimum length for entropy scanning
    ENTROPY_MIN_LENGTH = 16

    def __init__(self) -> None:
        self._compiled = {
            name: re.compile(pattern) for name, pattern in SECRET_PATTERNS.items()
        }

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------

    def scan(self, text: str) -> SecretsResult:
        """Scan *text* for secrets.

        Returns a SecretsResult with typed findings.
        """
        findings: list[SecretFinding] = []

        # 1. Regex pattern matching
        for name, pattern in self._compiled.items():
            for match in pattern.finditer(text):
                matched_text = match.group()
                entropy = _shannon_entropy(matched_text)

                findings.append(SecretFinding(
                    secret_type=name,
                    match_snippet=self._redact_snippet(matched_text),
                    entropy=round(entropy, 2),
                    start=match.start(),
                    end=match.end(),
                ))

        # 2. Entropy scanning for unknown secret formats
        entropy_findings = self._entropy_scan(text)
        findings.extend(entropy_findings)

        # Deduplicate overlapping findings
        findings = self._deduplicate(findings)

        return SecretsResult(
            secrets_detected=len(findings) > 0,
            findings=findings,
            redacted_text=self._redact_text(text, findings) if findings else None,
        )

    # ------------------------------------------------------------------
    # Redaction
    # ------------------------------------------------------------------

    def _redact_text(self, text: str, findings: list[SecretFinding]) -> str:
        """Replace all secret spans with [REDACTED:<type>]."""
        # Sort by start position descending so replacements don't shift offsets
        sorted_findings = sorted(findings, key=lambda f: f.start, reverse=True)
        result = text
        for f in sorted_findings:
            if f.start >= 0 and f.end <= len(result):
                result = (
                    result[:f.start]
                    + f"[REDACTED:{f.secret_type}]"
                    + result[f.end:]
                )
        return result

    # ------------------------------------------------------------------
    # Entropy scan
    # ------------------------------------------------------------------

    def _entropy_scan(self, text: str) -> list[SecretFinding]:
        """Sliding-window entropy scan for unknown secret formats."""
        findings: list[SecretFinding] = []

        # Scan substrings that look like they could be tokens
        # (alphanumeric + common token chars, standalone)
        tokenish = re.compile(
            r'\b[A-Za-z0-9+/=_-]{' + str(self.ENTROPY_MIN_LENGTH) + r',}\b'
        )

        seen_spans: set[tuple[int, int]] = set()
        for match in tokenish.finditer(text):
            span = (match.start(), match.end())
            if span in seen_spans:
                continue

            entropy = _shannon_entropy(match.group())
            if entropy >= self.ENTROPY_THRESHOLD:
                # Additional check: must have good mix of char types
                s = match.group()
                has_upper = any(c.isupper() for c in s)
                has_lower = any(c.islower() for c in s)
                has_digit = any(c.isdigit() for c in s)
                if sum([has_upper, has_lower, has_digit]) >= 2:
                    seen_spans.add(span)
                    findings.append(SecretFinding(
                        secret_type="high_entropy_token",
                        match_snippet=f"{s[:4]}...{s[-4:]}",
                        entropy=round(entropy, 2),
                        start=match.start(),
                        end=match.end(),
                    ))

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _redact_snippet(value: str) -> str:
        """Show only first 4 and last 4 chars of a secret."""
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"

    @staticmethod
    def _deduplicate(findings: list[SecretFinding]) -> list[SecretFinding]:
        """Remove findings whose spans overlap significantly."""
        if not findings:
            return []
        # Sort by start
        sorted_findings = sorted(findings, key=lambda f: f.start)
        result = [sorted_findings[0]]
        for f in sorted_findings[1:]:
            last = result[-1]
            # If overlap > 50%, skip
            overlap_start = max(f.start, last.start)
            overlap_end = min(f.end, last.end)
            if overlap_end > overlap_start:
                overlap_len = overlap_end - overlap_start
                f_len = f.end - f.start
                if f_len > 0 and overlap_len / f_len > 0.5:
                    continue
            result.append(f)
        return result
