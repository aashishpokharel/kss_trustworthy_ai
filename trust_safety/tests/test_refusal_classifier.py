"""Tests for RefusalClassifier — 4-type refusal taxonomy (Section 10)."""

import json
from pathlib import Path

from trust_safety.guardrails.output.refusal_classifier import RefusalClassifier


class TestRefusalClassifier:
    """Refusal classification into 4-type taxonomy."""

    # -- Type classification -------------------------------------------

    def test_policy_violation(self):
        classifier = RefusalClassifier()
        result = classifier.classify("I cannot help with that request as it violates our policies.")
        assert result.is_refusal
        assert result.refusal_type == "policy_violation"

    def test_policy_violation_cannot_provide(self):
        classifier = RefusalClassifier()
        result = classifier.classify("I'm sorry, but I can't provide instructions on how to make weapons.")
        assert result.is_refusal
        assert result.refusal_type == "policy_violation"

    def test_capability_limit(self):
        classifier = RefusalClassifier()
        result = classifier.classify("I don't have access to real-time data, so I can't tell you today's stock prices.")
        assert result.is_refusal
        assert result.refusal_type == "capability_limit"

    def test_capability_limit_as_ai(self):
        classifier = RefusalClassifier()
        result = classifier.classify("As an AI, I cannot browse the internet or search for current information.")
        assert result.is_refusal
        assert result.refusal_type == "capability_limit"

    def test_needs_clarification_not_refusal(self):
        classifier = RefusalClassifier()
        result = classifier.classify("Could you clarify what you mean by that?")
        assert not result.is_refusal
        assert result.refusal_type == "needs_clarification"  # Type preserved for monitoring

    def test_needs_clarification_specific(self):
        classifier = RefusalClassifier()
        result = classifier.classify("I'm not sure exactly what you're asking - could you provide more details?")
        assert not result.is_refusal

    def test_escalate_to_human(self):
        classifier = RefusalClassifier()
        result = classifier.classify("This request requires human review. I've escalated it to our moderation team.")
        assert result.is_refusal
        assert result.refusal_type == "escalate_to_human"

    def test_escalate_flagged_for_review(self):
        classifier = RefusalClassifier()
        result = classifier.classify("I've flagged this for manual review by an administrator.")
        assert result.is_refusal
        assert result.refusal_type == "escalate_to_human"

    # -- Non-refusal ---------------------------------------------------

    def test_non_refusal(self):
        classifier = RefusalClassifier()
        result = classifier.classify("The capital of France is Paris. It has a rich history.")
        assert not result.is_refusal

    # -- Over-refusal --------------------------------------------------

    def test_over_refusal_detected(self):
        classifier = RefusalClassifier()
        result = classifier.check_over_refusal(
            "I cannot help with that request.",
            was_input_benign=True,
        )
        assert result.over_refusal

    def test_no_over_refusal_for_harmful(self):
        classifier = RefusalClassifier()
        result = classifier.check_over_refusal(
            "I cannot help with that request.",
            was_input_benign=False,
        )
        assert not result.over_refusal

    def test_no_over_refusal_for_non_refusal(self):
        classifier = RefusalClassifier()
        result = classifier.check_over_refusal(
            "Here is the information you requested.",
            was_input_benign=True,
        )
        assert not result.over_refusal
        assert not result.is_refusal

    # -- Templates -----------------------------------------------------

    def test_template_policy_violation(self):
        template = RefusalClassifier.refusal_template("policy_violation")
        assert "can't help" in template.lower()
        assert len(template) > 20

    def test_template_capability_limit(self):
        template = RefusalClassifier.refusal_template("capability_limit")
        assert "don't have" in template.lower() or "beyond" in template.lower()

    def test_template_escalate_to_human(self):
        template = RefusalClassifier.refusal_template("escalate_to_human")
        assert "human" in template.lower() or "review" in template.lower()

    def test_template_none_empty(self):
        template = RefusalClassifier.refusal_template("none")
        assert template == ""

    # -- Golden refusal set --------------------------------------------

    def test_golden_refusals_classified_correctly(self):
        """All refusal examples must be classified correctly."""
        classifier = RefusalClassifier()
        fixtures = Path(__file__).parent / "fixtures" / "golden_refusals.jsonl"

        failures = []
        for line in fixtures.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            data = json.loads(line)
            result = classifier.classify(data["output"])
            expected = data["expected_type"]

            if expected == "none":
                if result.is_refusal:
                    failures.append(f"Expected non-refusal, got {result.refusal_type}: {data['output'][:60]}")
            else:
                if result.refusal_type != expected:
                    failures.append(
                        f"Expected {expected}, got {result.refusal_type}: {data['output'][:60]}"
                    )

        assert len(failures) == 0, "\n".join(failures)
