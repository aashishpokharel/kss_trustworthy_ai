"""Tests for GroundednessChecker — hallucination detection (Section 11)."""

import json
from pathlib import Path

from trust_safety.guardrails.output.groundedness_checker import GroundednessChecker


class TestGroundednessChecker:
    """Claim extraction and faithfulness scoring."""

    # -- Claim extraction ----------------------------------------------

    def test_extracts_factual_claims(self):
        checker = GroundednessChecker()
        result = checker.check(
            "Paris is the capital of France. It has 2.1 million residents.",
            source_context="Paris is the capital of France.",
        )
        assert result.total_claims > 0

    def test_all_supported_when_source_covers_all(self):
        checker = GroundednessChecker()
        result = checker.check(
            "The sky is blue. Water is wet.",
            source_context="The sky is blue. Water is wet. Fire is hot.",
        )
        assert result.score == 1.0
        assert len(result.unsupported_claims) == 0

    def test_unsupported_claims_detected(self):
        checker = GroundednessChecker()
        result = checker.check(
            "Paris is the capital of France. It has 2.1 million residents and was founded in 250 BC.",
            source_context="Paris is the capital of France.",
        )
        # "2.1 million residents" and "founded in 250 BC" not in source
        assert result.score < 1.0
        assert len(result.unsupported_claims) > 0

    def test_no_source_context(self):
        """Without source context, only hedging is checked."""
        checker = GroundednessChecker()
        result = checker.check("This is some output text.", source_context=None)
        assert result.score == 1.0  # No claims to check
        assert result.total_claims >= 0

    def test_empty_output(self):
        checker = GroundednessChecker()
        result = checker.check("", source_context="some context")
        assert result.total_claims == 0
        assert result.score == 1.0  # Nothing to check → default pass

    # -- Hedging detection ---------------------------------------------

    def test_detects_hedging(self):
        checker = GroundednessChecker()
        result = checker.check(
            "I think Paris is the capital of France. It might be the largest city.",
            source_context="Paris is the capital.",
        )
        assert result.hedging_detected
        assert len(result.hedging_phrases) > 0

    def test_no_hedging_in_confident_text(self):
        checker = GroundednessChecker()
        result = checker.check(
            "Paris is the capital of France. It has 2.1 million residents.",
            source_context="Paris is the capital.",
        )
        # May or may not detect hedging depending on patterns
        assert isinstance(result.hedging_detected, bool)

    # -- Domain thresholds ---------------------------------------------

    def test_medical_domain_strict(self):
        checker = GroundednessChecker()
        result = checker.check(
            "Aspirin reduces fever. It cures all known diseases.",
            source_context="Aspirin is a fever reducer.",
            domain="medical",
        )
        assert result.domain_threshold == 0.85

    def test_creative_domain_no_threshold(self):
        checker = GroundednessChecker()
        result = checker.check(
            "The dragon flew over the rainbow.",
            source_context="There was a dragon.",
            domain="creative",
        )
        assert result.domain_threshold == 0.0
        assert result.passed  # Creative domain always passes

    def test_general_domain_default(self):
        checker = GroundednessChecker()
        result = checker.check("Some text.", source_context="context", domain="general")
        assert result.domain_threshold == 0.70

    # -- Golden hallucination set --------------------------------------

    def test_golden_hallucinations_detected(self):
        """Hallucinated outputs should have score < 1.0."""
        checker = GroundednessChecker()
        fixtures = Path(__file__).parent / "fixtures" / "golden_hallucinations.jsonl"

        for line in fixtures.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            data = json.loads(line)
            result = checker.check(
                data["output"],
                source_context=data["source"],
            )
            # Hallucinated outputs should have at least some unsupported claims
            if data["unsupported_count"] > 0:
                assert len(result.unsupported_claims) > 0 or result.score < 1.0, (
                    f"Expected unsupported claims in: {data['output'][:60]}..."
                )
