"""
Refusal Classifier — classifies LLM refusals into 4 types (Section 10).

Taxonomy:
- policy_violation  — "I can't help with that" — correct refusal of harmful request
- capability_limit  — "I don't have access to real-time data" — honest limitation
- needs_clarification — "Could you clarify?" — not a refusal at all
- escalate_to_human  — "This requires human review" — HITL escalation

Over-refusal tracking: if a benign request was refused, flag it.
"""

from __future__ import annotations

import re

from trust_safety.guardrails.output.models import (
    RefusalClassification,
    RefusalType,
)


# ------------------------------------------------------------------
# Refusal pattern banks
# ------------------------------------------------------------------

POLICY_VIOLATION_PATTERNS = [
    r"(?i)\b(i\s+(cannot|can't|won't|will\s+not)\s+(help|assist|provide|answer|comply|do|fulfill)\b)",
    r"(?i)\b(i\s+(cannot|can't)\s+(engage|participate|respond)\b)",
    r"(?i)\b(against\s+(my|our)\s+(policies?|guidelines?|rules?|principles?))\b",
    r"(?i)\b(not\s+(appropriate|allowed|permitted|safe|ethical))\b",
    r"(?i)\b(i\s+(must|have\s+to)\s+(decline|refuse|reject))\b",
    r"(?i)\b(violates?\s+(the\s+)?(terms|policies?|guidelines?))\b",
]

CAPABILITY_LIMIT_PATTERNS = [
    r"(?i)\b(i\s+(don't|do\s+not)\s+have\s+(access\s+to|the\s+ability\s+to|information\s+about))\b",
    r"(?i)\b(i\s+(cannot|can't)\s+(access|browse|search|look\s+up|retrieve))\b",
    r"(?i)\b(as\s+(an\s+)?AI\b.*\b(i\s+(don't|do\s+not|cannot|can't)))\b",
    r"(?i)\b(my\s+(knowledge|training|data)\s+(only\s+goes|is\s+limited|cuts?\s+off))\b",
    r"(?i)\b(i\s+(don't|do\s+not)\s+(know|have\s+enough\s+information))\b",
    r"(?i)\b(i'm\s+(not|un)\s+able\s+to\b)",
]

NEEDS_CLARIFICATION_PATTERNS = [
    r"(?i)\b(could\s+you\s+(clarify|elaborate|specify|explain|provide\s+more))\b",
    r"(?i)\b(i\s+(need|would\s+need)\s+(more|additional|further)\s+(information|context|details?|clarification))\b",
    r"(?i)\b(can\s+you\s+(be\s+more\s+specific|tell\s+me\s+more|rephrase))\b",
    r"(?i)\b(what\s+(exactly|specifically|precisely)\s+(do\s+you|are\s+you))\b",
    r"(?i)\b(i'm\s+not\s+sure\s+(what|i\s+understand|exactly\s+what|.*what))\b",
    r"(?i)\b(clarify|elaborate|specify)\b.*\b(mean|asking|need|want)\b",
    r"(?i)\b(more\s+(specific|details?|information|context))\b",
]

ESCALATE_TO_HUMAN_PATTERNS = [
    r"(?i)\b(this\s+(requires?|needs?|should\s+involve)\s+(human|manual)\s+(review|approval|intervention|oversight))\b",
    r"(?i)\b(i('ve|'ll|have|will)\s+(escalated?|forwarded?|referred?|routed?)\s+(this|it)\s+to\b)",
    r"(?i)\b(a\s+human\s+(reviewer|operator|agent|moderator|administrator))\b",
    r"(?i)\b(please\s+(contact|reach\s+out\s+to|speak\s+with)\s+(a|our|your)\s+(human|support|team))\b",
    r"(?i)\b(flagged?\s+(this|it|that|for)\s+(for\s+)?(human|manual|admin)\s+review)\b",
]


# ------------------------------------------------------------------
# RefusalClassifier
# ------------------------------------------------------------------

class RefusalClassifier:
    """Classify LLM refusals into the 4-type taxonomy (Section 10).

    Usage::

        classifier = RefusalClassifier()
        result = classifier.classify("I can't help with that request.")
        # RefusalClassification(is_refusal=True, refusal_type="policy_violation", ...)
    """

    def __init__(self) -> None:
        self._policy_patterns = [re.compile(p) for p in POLICY_VIOLATION_PATTERNS]
        self._capability_patterns = [re.compile(p) for p in CAPABILITY_LIMIT_PATTERNS]
        self._clarify_patterns = [re.compile(p) for p in NEEDS_CLARIFICATION_PATTERNS]
        self._escalate_patterns = [re.compile(p) for p in ESCALATE_TO_HUMAN_PATTERNS]

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify(self, output_text: str) -> RefusalClassification:
        """Classify *output_text* as a refusal type or non-refusal."""
        if not output_text or not output_text.strip():
            return RefusalClassification(is_refusal=False)

        # Score each type
        scores: dict[RefusalType, int] = {
            "policy_violation": self._count_matches(output_text, self._policy_patterns),
            "capability_limit": self._count_matches(output_text, self._capability_patterns),
            "needs_clarification": self._count_matches(output_text, self._clarify_patterns),
            "escalate_to_human": self._count_matches(output_text, self._escalate_patterns),
        }

        max_type: RefusalType = "none"
        max_score = 0
        for rtype, score in scores.items():
            if score > max_score:
                max_score = score
                max_type = rtype

        is_refusal = max_score > 0 and max_type not in ("needs_clarification", "none")
        # needs_clarification is NOT a refusal — it's asking for more info,
        # but we still report the type for monitoring

        return RefusalClassification(
            is_refusal=is_refusal,
            refusal_type=max_type if max_score > 0 else "none",
            confidence=min(1.0, max_score * 0.3) if max_score > 0 else 0.0,
            over_refusal=False,
        )

    # ------------------------------------------------------------------
    # Over-refusal detection
    # ------------------------------------------------------------------

    def check_over_refusal(
        self, output_text: str, was_input_benign: bool
    ) -> RefusalClassification:
        """Classify AND check for over-refusal.

        If *was_input_benign* is True and the output is a refusal,
        flag as over-refusal.
        """
        result = self.classify(output_text)
        if result.is_refusal and was_input_benign:
            result.over_refusal = True
        return result

    # ------------------------------------------------------------------
    # Templates per type
    # ------------------------------------------------------------------

    @staticmethod
    def refusal_template(refusal_type: RefusalType) -> str:
        """Return the appropriate refusal template for each type (Section 10).

        Templates are short, non-judgmental, and offer safe alternatives
        where applicable.
        """
        templates: dict[RefusalType, str] = {
            "policy_violation": (
                "I can't help with that request. If you have a different "
                "question I can assist with, please ask."
            ),
            "capability_limit": (
                "I don't have the ability to do that — it's beyond my "
                "current capabilities. Is there something else I can help with?"
            ),
            "needs_clarification": (
                "I need more information to answer that. Could you provide "
                "additional details?"
            ),
            "escalate_to_human": (
                "This request has been flagged for human review. A reviewer "
                "will follow up shortly."
            ),
            "none": "",
        }
        return templates.get(refusal_type, "")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_matches(text: str, patterns: list[re.Pattern]) -> int:
        """Count how many patterns match in the text (max 1 per pattern)."""
        count = 0
        for pattern in patterns:
            if pattern.search(text):
                count += 1
        return count
