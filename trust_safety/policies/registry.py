"""
Policy Registry — config-driven compliance profile management.

Compliance profiles can be added, removed, or combined at runtime via
configuration.  The registry uses conservative merging: when multiple
profiles are active, the strictest rule from each field wins.
"""

from __future__ import annotations

from pydantic import BaseModel

from trust_safety.models.base import DataTier
from trust_safety.policies.defaults import (
    BUILTIN_PROFILES,
    ComplianceProfile,
    ComplianceProfileConfig,
    DataHandlingRule,
)


class PolicyRegistry(BaseModel):
    """Central registry of compliance profiles.

    Profiles can be activated by name (via Settings.policy_profiles).
    When multiple profiles are active, rules are combined conservatively:
    the most restrictive value from each field wins.
    """

    _profiles: dict[ComplianceProfile, ComplianceProfileConfig] = {}

    def __init__(self, **data):
        super().__init__(**data)
        # Load built-in defaults on construction
        for profile, config in BUILTIN_PROFILES.items():
            self._profiles[profile] = config

    # -- Lookup -------------------------------------------------------

    def get_profile(self, name: ComplianceProfile) -> ComplianceProfileConfig:
        """Return the config for a single compliance profile."""
        if name not in self._profiles:
            raise ValueError(f"Unknown compliance profile: {name}")
        return self._profiles[name]

    def get_profile_by_name(self, name: str) -> ComplianceProfileConfig:
        """String-based lookup — useful for config-driven activation."""
        try:
            profile = ComplianceProfile(name)
        except ValueError:
            raise ValueError(f"Unknown compliance profile: '{name}'")
        return self.get_profile(profile)

    def list_profiles(self) -> list[ComplianceProfileConfig]:
        """Return all available profiles."""
        return list(self._profiles.values())

    # -- Combining profiles -------------------------------------------

    def combine_profiles(
        self, profiles: list[ComplianceProfile]
    ) -> ComplianceProfileConfig:
        """Merge multiple profiles using conservative (most-restrictive) rules.

        For each DataHandlingRule field, the *most restrictive* value across
        all input profiles is selected.  Examples:
        * If any profile says ``allow_third_party_processing=False``, the
          combined result is ``False``.
        * If any profile says ``restricted_tier_allowed=False``, the
          combined result is ``False``.
        * The *minimum* max_retention_days across profiles is used.
        * The *strictest* pii_treatment is used
          (block > redact > tokenize > allow_with_consent).

        If *profiles* is empty, the NONE profile is returned.
        """
        if not profiles:
            return self.get_profile(ComplianceProfile.NONE)

        configs = [self.get_profile(p) for p in profiles]

        # Conservative merge of DataHandlingRule fields
        combined_rule = DataHandlingRule(
            max_retention_days=min(c.data_handling.max_retention_days for c in configs),
            allow_third_party_processing=all(
                c.data_handling.allow_third_party_processing for c in configs
            ),
            require_consent=any(
                c.data_handling.require_consent for c in configs
            ),
            require_dp_agreement=any(
                c.data_handling.require_dp_agreement for c in configs
            ),
            pii_treatment=self._strictest_pii_treatment(
                [c.data_handling.pii_treatment for c in configs]
            ),
            restricted_tier_allowed=all(
                c.data_handling.restricted_tier_allowed for c in configs
            ),
        )

        combined_name = " + ".join(p.value.upper() for p in profiles)
        return ComplianceProfileConfig(
            name=ComplianceProfile.NONE,  # Sentinel — this is a synthetic profile
            description=f"Conservative merge of: {combined_name}",
            data_handling=combined_rule,
        )

    # -- Data tier validation -----------------------------------------

    def validate_data_tier(
        self, tier: DataTier, profile: ComplianceProfile
    ) -> bool:
        """Check whether *tier* is allowed under *profile*.

        Returns True if data of this tier may enter the pipeline.
        """
        config = self.get_profile(profile)
        if tier == DataTier.RESTRICTED:
            return config.data_handling.restricted_tier_allowed
        # PUBLIC, INTERNAL, CONFIDENTIAL are allowed by default;
        # additional per-tier rules can be added here in future phases.
        return True

    # -- Helpers ------------------------------------------------------

    @staticmethod
    def _strictest_pii_treatment(
        treatments: list[str],
    ) -> str:
        """Return the strictest PII treatment from a list.

        Strictness order: block > redact > tokenize > allow_with_consent
        """
        order = {"block": 3, "redact": 2, "tokenize": 1, "allow_with_consent": 0}
        return max(treatments, key=lambda t: order.get(t, 0))
