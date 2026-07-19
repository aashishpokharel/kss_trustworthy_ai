"""Tests for ComplianceProfile, DataHandlingRule, ComplianceProfileConfig, PolicyRegistry."""

import pytest

from trust_safety.models.base import DataTier
from trust_safety.policies.defaults import (
    BUILTIN_PROFILES,
    ComplianceProfile,
    ComplianceProfileConfig,
    DataHandlingRule,
)
from trust_safety.policies.registry import PolicyRegistry


class TestComplianceProfileConfig:
    """Built-in profiles must load with correct defaults."""

    def test_all_profiles_loadable(self):
        """Every built-in profile must be constructable."""
        for profile in ComplianceProfile:
            assert profile in BUILTIN_PROFILES, f"Missing built-in for {profile}"

    def test_none_is_permissive(self):
        """NONE profile allows third-party processing, no consent required."""
        cfg = BUILTIN_PROFILES[ComplianceProfile.NONE]
        assert cfg.data_handling.allow_third_party_processing is True
        assert cfg.data_handling.require_consent is False
        assert cfg.data_handling.require_dp_agreement is False

    def test_gdpr_is_strict(self):
        """GDPR requires consent + DPA, blocks restricted tier."""
        cfg = BUILTIN_PROFILES[ComplianceProfile.GDPR]
        assert cfg.data_handling.require_consent is True
        assert cfg.data_handling.require_dp_agreement is True
        assert cfg.data_handling.allow_third_party_processing is False
        assert cfg.data_handling.restricted_tier_allowed is False

    def test_hipaa_blocks_restricted(self):
        """HIPAA blocks restricted tier by default."""
        cfg = BUILTIN_PROFILES[ComplianceProfile.HIPAA]
        assert cfg.data_handling.restricted_tier_allowed is False

    def test_gdpr_stricter_than_none(self):
        """NONE should be more permissive than GDPR in every field."""
        none = BUILTIN_PROFILES[ComplianceProfile.NONE].data_handling
        gdpr = BUILTIN_PROFILES[ComplianceProfile.GDPR].data_handling
        # GDPR max retention <= NONE max retention
        assert gdpr.max_retention_days <= none.max_retention_days
        # If NONE allows 3rd party, GDPR may not
        assert not gdpr.allow_third_party_processing or none.allow_third_party_processing


class TestDataHandlingRule:
    """DataHandlingRule validation and defaults."""

    def test_default_restricted_tier_allowed_false(self):
        """Fail-closed: restricted_tier_allowed defaults to False."""
        rule = DataHandlingRule()
        assert rule.restricted_tier_allowed is False

    def test_default_pii_treatment_redact(self):
        """Default PII treatment is redact."""
        rule = DataHandlingRule()
        assert rule.pii_treatment == "redact"

    def test_invalid_pii_treatment(self):
        """Only valid Literal values accepted."""
        with pytest.raises(ValueError):
            DataHandlingRule(pii_treatment="delete_everything")


class TestPolicyRegistry:
    """PolicyRegistry — composable compliance profiles."""

    def test_get_profile(self, policy_registry: PolicyRegistry):
        """get_profile returns the correct config."""
        cfg = policy_registry.get_profile(ComplianceProfile.GDPR)
        assert cfg.name == ComplianceProfile.GDPR

    def test_get_profile_by_name_string(self, policy_registry: PolicyRegistry):
        """String-based lookup works."""
        cfg = policy_registry.get_profile_by_name("gdpr")
        assert cfg.data_handling.require_consent is True

    def test_get_profile_by_name_unknown(self, policy_registry: PolicyRegistry):
        """Unknown profile name raises ValueError."""
        with pytest.raises(ValueError):
            policy_registry.get_profile_by_name("made_up_compliance")

    def test_list_profiles(self, policy_registry: PolicyRegistry):
        """list_profiles returns all built-in profiles."""
        profiles = policy_registry.list_profiles()
        assert len(profiles) == 4
        names = {p.name for p in profiles}
        assert ComplianceProfile.GDPR in names
        assert ComplianceProfile.HIPAA in names

    # -- combine_profiles ----------------------------------------------

    def test_combine_empty_returns_none(self, policy_registry: PolicyRegistry):
        """Empty list → NONE profile."""
        combined = policy_registry.combine_profiles([])
        assert combined.name == ComplianceProfile.NONE

    def test_combine_single_returns_same(self, policy_registry: PolicyRegistry):
        """Combining one profile returns its rules."""
        combined = policy_registry.combine_profiles([ComplianceProfile.GDPR])
        gdpr = policy_registry.get_profile(ComplianceProfile.GDPR)
        assert combined.data_handling.require_consent == gdpr.data_handling.require_consent

    def test_combine_most_restrictive_consent(self, policy_registry: PolicyRegistry):
        """If ANY profile requires consent, combined result requires it."""
        # NONE doesn't require consent, GDPR does → combined should
        combined = policy_registry.combine_profiles(
            [ComplianceProfile.NONE, ComplianceProfile.GDPR]
        )
        assert combined.data_handling.require_consent is True

    def test_combine_most_restrictive_retention(self, policy_registry: PolicyRegistry):
        """Minimum retention days across profiles is used."""
        # NONE = 365, GDPR = 30 → combined = 30
        combined = policy_registry.combine_profiles(
            [ComplianceProfile.NONE, ComplianceProfile.GDPR]
        )
        assert combined.data_handling.max_retention_days == 30

    def test_combine_gdpr_hipaa_restrictive(self, policy_registry: PolicyRegistry):
        """GDPR + HIPAA is at least as strict as each individually."""
        combined = policy_registry.combine_profiles(
            [ComplianceProfile.GDPR, ComplianceProfile.HIPAA]
        )
        assert combined.data_handling.require_consent is True
        assert combined.data_handling.require_dp_agreement is True
        assert combined.data_handling.restricted_tier_allowed is False

    def test_combine_most_restrictive_pii(self, policy_registry: PolicyRegistry):
        """CCPA uses tokenize, GDPR uses redact → combined uses redact (stricter)."""
        combined = policy_registry.combine_profiles(
            [ComplianceProfile.CCPA, ComplianceProfile.GDPR]
        )
        assert combined.data_handling.pii_treatment == "redact"

    def test_combine_all(self, policy_registry: PolicyRegistry):
        """Combining all profiles returns a valid config."""
        combined = policy_registry.combine_profiles(list(ComplianceProfile))
        assert combined.data_handling.restricted_tier_allowed is False

    # -- validate_data_tier --------------------------------------------

    def test_validate_public_allowed(self, policy_registry: PolicyRegistry):
        """PUBLIC tier is always allowed."""
        assert policy_registry.validate_data_tier(
            DataTier.PUBLIC, ComplianceProfile.GDPR
        ) is True

    def test_validate_restricted_blocked_gdpr(self, policy_registry: PolicyRegistry):
        """RESTRICTED tier is blocked under GDPR."""
        assert policy_registry.validate_data_tier(
            DataTier.RESTRICTED, ComplianceProfile.GDPR
        ) is False

    def test_validate_restricted_blocked_hipaa(self, policy_registry: PolicyRegistry):
        """RESTRICTED tier is blocked under HIPAA."""
        assert policy_registry.validate_data_tier(
            DataTier.RESTRICTED, ComplianceProfile.HIPAA
        ) is False

    def test_validate_confidential_allowed(self, policy_registry: PolicyRegistry):
        """CONFIDENTIAL tier is allowed (not blocked by default)."""
        assert policy_registry.validate_data_tier(
            DataTier.CONFIDENTIAL, ComplianceProfile.GDPR
        ) is True
