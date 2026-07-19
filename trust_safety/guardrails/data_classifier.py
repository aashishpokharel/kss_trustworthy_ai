"""
Data Classifier — rules-based classification into the 4-tier model (Section 4).

| Tier        | Trigger                                         |
|-------------|-------------------------------------------------|
| PUBLIC      | No PII, no secrets, no sensitive topics         |
| INTERNAL    | (default for unclassified content)              |
| CONFIDENTIAL| PII detected, or business-sensitive keywords     |
| RESTRICTED  | Secrets detected, or health/government keywords |

Integrates with PII and secrets scanner results from the input pipeline.
"""

from __future__ import annotations

import re

from trust_safety.guardrails.input.models import PIIResult, SecretsResult
from trust_safety.models.base import DataTier

# ------------------------------------------------------------------
# Keyword patterns that escalate data tier
# ------------------------------------------------------------------

CONFIDENTIAL_PATTERNS = [
    r'(?i)\b(contract|financial|salary|revenue|profit|budget|payroll)\b',
    r'(?i)\b(employee|personnel|hr\s+record|performance\s+review)\b',
    r'(?i)\b(legal\s+review|attorney|litigation|settlement)\b',
    r'(?i)\b(merger|acquisition|divestiture|ipo|pre-ipo)\b',
]

RESTRICTED_PATTERNS = [
    r'(?i)\b(health\s+record|medical\s+history|diagnosis|patient)\b',
    r'(?i)\b(biometric|fingerprint|retina\s+scan|dna\s+profile)\b',
    r'(?i)\b(passport\s+number|national\s+id|government\s+id)\b',
    r'(?i)\b(classified|top\s+secret|clearance|security\s+clearance)\b',
    r'(?i)\b(credit\s+card\s+number|bank\s+account|routing\s+number)\b',
]


# ------------------------------------------------------------------
# DataClassifier
# ------------------------------------------------------------------

class DataClassifier:
    """Rules-based data tier classifier.

    Usage::

        classifier = DataClassifier()
        tier = classifier.classify(text, pii_result, secrets_result)
    """

    _compiled_confidential: list[re.Pattern] = []
    _compiled_restricted: list[re.Pattern] = []
    _built: bool = False

    def __init__(self) -> None:
        if not DataClassifier._built:
            DataClassifier._compiled_confidential = [
                re.compile(p) for p in CONFIDENTIAL_PATTERNS
            ]
            DataClassifier._compiled_restricted = [
                re.compile(p) for p in RESTRICTED_PATTERNS
            ]
            DataClassifier._built = True

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify(
        self,
        text: str,
        pii_result: PIIResult | None = None,
        secrets_result: SecretsResult | None = None,
    ) -> DataTier:
        """Classify *text* into a DataTier.

        Decision logic (first match wins, from most to least restrictive):
        1. RESTRICTED if secrets detected or restricted keywords match
        2. CONFIDENTIAL if PII detected or confidential keywords match
        3. INTERNAL if unclassified (default)
        4. PUBLIC if no sensitive content at all
        """
        # -- RESTRICTED triggers --
        if secrets_result and secrets_result.secrets_detected:
            return DataTier.RESTRICTED

        for pattern in self._compiled_restricted:
            if pattern.search(text):
                return DataTier.RESTRICTED

        # -- CONFIDENTIAL triggers --
        if pii_result and pii_result.pii_detected:
            return DataTier.CONFIDENTIAL

        for pattern in self._compiled_confidential:
            if pattern.search(text):
                return DataTier.CONFIDENTIAL

        # -- PUBLIC vs INTERNAL --
        # Heuristic: if the text contains any business/organizational language,
        # classify as INTERNAL.  Otherwise PUBLIC.
        if self._looks_internal(text):
            return DataTier.INTERNAL

        return DataTier.PUBLIC

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_internal(text: str) -> bool:
        """Heuristic: does this content seem like internal business data?"""
        internal_indicators = [
            r'(?i)\b(wiki|confluence|sharepoint|jira|slack|teams)\b',
            r'(?i)\b(internal|confidential|proprietary)\b',
            r'(?i)\b(meeting|agenda|minutes|action\s+item)\b',
            r'(?i)\b(okr|kpi|quarterly|roadmap|sprint)\b',
            r'(?i)\b(engineering|product|design|marketing|sales)\s+(team|department)\b',
        ]
        for pattern in internal_indicators:
            if re.search(pattern, text):
                return True
        return False
