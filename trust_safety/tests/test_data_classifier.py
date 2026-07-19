"""Tests for DataClassifier — rules-based tier classification."""

from trust_safety.guardrails.data_classifier import DataClassifier
from trust_safety.guardrails.input.models import PIIFinding, PIIResult, SecretFinding, SecretsResult
from trust_safety.models.base import DataTier


class TestDataClassifier:
    """Rules-based data tier classification (Section 4)."""

    # -- Normal text ---------------------------------------------------

    def test_public_text(self):
        classifier = DataClassifier()
        tier = classifier.classify("What is the capital of France?")
        assert tier == DataTier.PUBLIC

    def test_internal_text(self):
        classifier = DataClassifier()
        tier = classifier.classify(
            "The engineering team is working on the Q4 roadmap. "
            "Please review the sprint goals in Jira."
        )
        assert tier in (DataTier.INTERNAL, DataTier.PUBLIC)

    # -- PII → CONFIDENTIAL -------------------------------------------

    def test_pii_triggers_confidential(self):
        classifier = DataClassifier()
        pii_result = PIIResult(
            pii_detected=True,
            findings=[PIIFinding(
                entity_type="EMAIL_ADDRESS",
                value_snippet="[REDACTED]",
                start=0, end=20, score=0.9,
            )],
        )
        tier = classifier.classify("my email is john@example.com", pii_result=pii_result)
        assert tier == DataTier.CONFIDENTIAL

    # -- Secrets → RESTRICTED -----------------------------------------

    def test_secrets_triggers_restricted(self):
        classifier = DataClassifier()
        secrets_result = SecretsResult(
            secrets_detected=True,
            findings=[SecretFinding(
                secret_type="openai_api_key",
                match_snippet="sk-pr...wx234",
                entropy=4.5, start=0, end=56,
            )],
        )
        tier = classifier.classify(
            "API key: sk-proj-abc123",
            secrets_result=secrets_result,
        )
        assert tier == DataTier.RESTRICTED

    # -- Keyword triggers ---------------------------------------------

    def test_confidential_keywords(self):
        classifier = DataClassifier()
        tier = classifier.classify("The Q4 financial report shows revenue growth of 15%.")
        assert tier == DataTier.CONFIDENTIAL

    def test_restricted_keywords_medical(self):
        classifier = DataClassifier()
        tier = classifier.classify(
            "Patient medical history: diagnosed with hypertension. "
            "Prescribed medication for 30 days."
        )
        assert tier == DataTier.RESTRICTED

    def test_restricted_keywords_government_id(self):
        classifier = DataClassifier()
        tier = classifier.classify("Passport number and national ID are required for verification.")
        assert tier == DataTier.RESTRICTED

    # -- Empty / edge cases --------------------------------------------

    def test_empty_text(self):
        classifier = DataClassifier()
        tier = classifier.classify("")
        assert tier == DataTier.PUBLIC  # Empty is not sensitive

    # -- Tier ordering ------------------------------------------------

    def test_restricted_trumps_confidential(self):
        """If both PII and secrets are present, RESTRICTED wins."""
        classifier = DataClassifier()
        pii_result = PIIResult(
            pii_detected=True,
            findings=[PIIFinding(
                entity_type="EMAIL_ADDRESS", value_snippet="x", start=0, end=0, score=0.9,
            )],
        )
        secrets_result = SecretsResult(
            secrets_detected=True,
            findings=[SecretFinding(
                secret_type="openai_api_key", match_snippet="x", entropy=4.5,
            )],
        )
        tier = classifier.classify(
            "text", pii_result=pii_result, secrets_result=secrets_result,
        )
        assert tier == DataTier.RESTRICTED
