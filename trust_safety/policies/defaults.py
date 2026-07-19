"""
Compliance profile types and built-in default configurations.

This module defines the core types (ComplianceProfile, DataHandlingRule,
ComplianceProfileConfig) to avoid circular imports with registry.py.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Compliance profile enum
# ------------------------------------------------------------------

class ComplianceProfile(str, Enum):
    """Known compliance regimes.

    To add a new one:
    1. Add an enum value here
    2. Add a corresponding ComplianceProfileConfig below
    3. Add it to BUILTIN_PROFILES
    """

    NONE = "none"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"


# ------------------------------------------------------------------
# Data handling rules
# ------------------------------------------------------------------

class DataHandlingRule(BaseModel):
    """Rules that govern how data is treated under a compliance profile."""

    max_retention_days: int = Field(
        default=90, ge=0, description="Max days to retain data. 0 = no retention."
    )
    allow_third_party_processing: bool = Field(
        default=True,
        description="Can data be sent to third-party processors?",
    )
    require_consent: bool = Field(
        default=False,
        description="Must the data subject consent before processing?",
    )
    require_dp_agreement: bool = Field(
        default=False,
        description="Is a Data Processing Agreement (DPA/BAA) required?",
    )
    pii_treatment: Literal["redact", "tokenize", "allow_with_consent", "block"] = Field(
        default="redact",
        description="How to handle PII: redact, tokenize (reversible), "
                    "allow with consent, or block entirely.",
    )
    restricted_tier_allowed: bool = Field(
        default=False,
        description="Can RESTRICTED-tier data enter the pipeline at all?  "
                    "Default False (fail-closed).",
    )


# ------------------------------------------------------------------
# Compliance profile config
# ------------------------------------------------------------------

class ComplianceProfileConfig(BaseModel):
    """A named compliance profile with its data handling rules."""

    name: ComplianceProfile
    description: str = ""
    data_handling: DataHandlingRule = Field(default_factory=DataHandlingRule)


# ------------------------------------------------------------------
# Built-in default profiles
# ------------------------------------------------------------------

NONE_PROFILE = ComplianceProfileConfig(
    name=ComplianceProfile.NONE,
    description="Baseline rules — no specific compliance regime active.",
    data_handling=DataHandlingRule(
        max_retention_days=365,
        allow_third_party_processing=True,
        require_consent=False,
        require_dp_agreement=False,
        pii_treatment="redact",
        restricted_tier_allowed=False,
    ),
)

GDPR_PROFILE = ComplianceProfileConfig(
    name=ComplianceProfile.GDPR,
    description="EU GDPR rules: consent required, restricted data blocked "
                "without DPA, PII redacted by default.",
    data_handling=DataHandlingRule(
        max_retention_days=30,
        allow_third_party_processing=False,
        require_consent=True,
        require_dp_agreement=True,
        pii_treatment="redact",
        restricted_tier_allowed=False,
    ),
)

HIPAA_PROFILE = ComplianceProfileConfig(
    name=ComplianceProfile.HIPAA,
    description="US HIPAA rules: PHI must be redacted, restricted tier "
                "always blocked, requires DPA/BAA.",
    data_handling=DataHandlingRule(
        max_retention_days=90,
        allow_third_party_processing=False,
        require_consent=True,
        require_dp_agreement=True,
        pii_treatment="redact",
        restricted_tier_allowed=False,
    ),
)

CCPA_PROFILE = ComplianceProfileConfig(
    name=ComplianceProfile.CCPA,
    description="California CCPA rules: right to know, right to delete, "
                "opt-out of sale.",
    data_handling=DataHandlingRule(
        max_retention_days=90,
        allow_third_party_processing=False,
        require_consent=True,
        require_dp_agreement=False,
        pii_treatment="tokenize",
        restricted_tier_allowed=False,
    ),
)

BUILTIN_PROFILES: dict[ComplianceProfile, ComplianceProfileConfig] = {
    ComplianceProfile.NONE: NONE_PROFILE,
    ComplianceProfile.GDPR: GDPR_PROFILE,
    ComplianceProfile.HIPAA: HIPAA_PROFILE,
    ComplianceProfile.CCPA: CCPA_PROFILE,
}
