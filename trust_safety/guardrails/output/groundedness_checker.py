"""
Groundedness / Hallucination Checker (Section 11).

Cheapest-first approach:
1. Claim extraction — split into sentences, identify factual claims
2. Citation requirement — claims must cite source chunks
3. Faithfulness scoring — keyword overlap between claim and source context
4. Hedging detection — uncertainty markers as a quality signal
5. Domain-specific thresholds — stricter for medical/legal, looser for creative
"""

from __future__ import annotations

import re
from typing import Literal

from trust_safety.guardrails.output.models import GroundednessResult

# ------------------------------------------------------------------
# Hedging / uncertainty markers
# ------------------------------------------------------------------

HEDGING_PATTERNS = [
    r'(?i)\b(i\s+think|i\s+believe|probably|maybe|perhaps|possibly)\b',
    r'(?i)\b(i\'?m\s+not\s+sure|i\s+cannot\s+(confirm|verify|guarantee))\b',
    r'(?i)\b(might\s+be|could\s+be|may\s+be|seems?\s+(like|to\s+be))\b',
    r'(?i)\b(approximately|roughly|around|about|estimated?)\b',
    r'(?i)\b(as\s+(an\s+)?ai|as\s+a\s+language\s+model)\b',
    r'(?i)\b(please\s+verify|you\s+should\s+check|consult\s+a\s+professional)\b',
]

# ------------------------------------------------------------------
# Factual claim indicators
# ------------------------------------------------------------------

FACTUAL_CLAIM_PATTERNS = [
    # Claims about specific facts, numbers, dates, named entities
    r'\b\d{4}\b',             # Years
    r'\b\d+%',                # Percentages
    r'\b\d+\s*(million|billion|thousand)\b',  # Large numbers
    r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # Proper names
    r'(?i)\b(according\s+to|studies?\s+show|research\s+indicates?)\b',
    r'(?i)\b(is|are|was|were|has|have|had)\s+(the|a|an)\b',  # Definitive statements
]

# ------------------------------------------------------------------
# Domain thresholds (Section 11)
# ------------------------------------------------------------------

DOMAIN_THRESHOLDS: dict[str, float] = {
    "medical": 0.85,
    "legal": 0.85,
    "financial": 0.80,
    "general": 0.70,
    "creative": 0.0,  # No threshold — log only
}

DomainType = Literal["general", "medical", "legal", "financial", "creative"]


# ------------------------------------------------------------------
# GroundednessChecker
# ------------------------------------------------------------------

class GroundednessChecker:
    """Check whether LLM output claims are supported by source context.

    Usage::

        checker = GroundednessChecker()
        result = checker.check(
            "Paris is the capital of France. It has 2.1 million people.",
            source_context="Paris is the capital of France.",
            domain="general",
        )
    """

    def __init__(self) -> None:
        self._hedging_compiled = [re.compile(p) for p in HEDGING_PATTERNS]

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def check(
        self,
        output_text: str,
        source_context: str | None = None,
        domain: DomainType = "general",
    ) -> GroundednessResult:
        """Check groundedness of *output_text* against *source_context*.

        If *source_context* is None, only hedging detection runs
        (useful when no retrieval context is available).
        """
        # 1. Extract claims
        claims = self._extract_claims(output_text)
        total_claims = len(claims)

        # 2. Check hedging
        hedging_phrases = self._detect_hedging(output_text)

        # 3. Check claim support against source context
        supported = 0
        unsupported: list[str] = []

        if source_context and claims:
            source_lower = source_context.lower()
            for claim in claims:
                if self._is_supported(claim, source_lower):
                    supported += 1
                else:
                    unsupported.append(claim)

        # 4. Compute score
        if source_context and total_claims > 0:
            score = supported / total_claims
        elif not source_context:
            score = 1.0  # No source to verify against → assume pass
        else:
            score = 1.0  # No factual claims → nothing to check

        # 5. Citation density (simplified: count "[N]" or "(source)" patterns)
        citation_density = self._citation_density(output_text, total_claims)

        # 6. Domain threshold
        threshold = DOMAIN_THRESHOLDS.get(domain, 0.70)
        passed = score >= threshold

        return GroundednessResult(
            score=round(score, 3),
            total_claims=total_claims,
            supported_claims=supported,
            unsupported_claims=unsupported[:10],  # Cap at 10
            citation_density=round(citation_density, 3),
            hedging_detected=len(hedging_phrases) > 0,
            hedging_phrases=hedging_phrases[:10],
            passed=passed,
            domain_threshold=threshold,
        )

    # ------------------------------------------------------------------
    # Claim extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract factual claims from text.

        Splits on sentence boundaries, then filters for sentences
        that look like factual statements.
        """
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims: list[str] = []

        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue

            # Check if sentence looks factual
            has_factual_marker = any(
                re.search(p, sent) for p in FACTUAL_CLAIM_PATTERNS
            )
            # Questions and imperatives are not claims
            is_claim = (
                not sent.endswith("?")
                and not sent.startswith(("Do ", "Can ", "Will ", "Would ", "Please "))
                and (has_factual_marker or len(sent.split()) >= 5)
            )

            if is_claim:
                claims.append(sent)

        return claims

    # ------------------------------------------------------------------
    # Claim support check
    # ------------------------------------------------------------------

    @staticmethod
    def _is_supported(claim: str, source_lower: str) -> bool:
        """Check if *claim* is supported by *source_lower*.

        Uses keyword overlap heuristic — extract significant words from
        the claim and check if they appear in the source context.
        """
        # Extract significant words (nouns, numbers, proper names)
        claim_lower = claim.lower()
        words = re.findall(r'\b[a-z]{4,}\b', claim_lower)
        numbers = re.findall(r'\b\d+\b', claim)

        # Need at least 2 significant words to check
        significant = words + numbers
        if len(significant) < 2:
            return True  # Too short to verify — give benefit of doubt

        # Count how many significant words appear in source
        matches = sum(1 for w in significant if w in source_lower)
        ratio = matches / len(significant) if significant else 0

        # If >50% of significant words appear in source, consider it supported
        return ratio >= 0.5

    # ------------------------------------------------------------------
    # Citation density
    # ------------------------------------------------------------------

    @staticmethod
    def _citation_density(text: str, total_claims: int) -> float:
        """Estimate citation density from citation markers in text."""
        # Count citation markers like [1], [2], (Author, Year), etc.
        citations = len(re.findall(r'\[\d+\]|\([^)]+\d{4}\)', text))
        if total_claims > 0:
            return min(1.0, citations / total_claims)
        return 0.0

    # ------------------------------------------------------------------
    # Hedging detection
    # ------------------------------------------------------------------

    def _detect_hedging(self, text: str) -> list[str]:
        """Detect hedging and uncertainty markers in output."""
        found: list[str] = []
        for pattern in self._hedging_compiled:
            for match in pattern.finditer(text):
                found.append(match.group())
        return list(set(found))  # Deduplicate
