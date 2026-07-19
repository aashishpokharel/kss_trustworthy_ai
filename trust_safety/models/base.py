"""
Foundational enums used by every other module.

- DataTier  — the 4-tier classification from Section 4 of the architecture
- TrustLevelEnum — how much we trust a given piece of content
"""

from enum import Enum


class DataTier(str, Enum):
    """Data classification tier per Section 4 of the architecture.

    | Tier       | Examples                          | Rule                                      |
    |------------|-----------------------------------|-------------------------------------------|
    | PUBLIC     | Marketing copy, public docs       | Freely usable, no restrictions             |
    | INTERNAL   | Internal wikis, non-sensitive data| Usable in-context, no third-party logs     |
    | CONFIDENTIAL| Contracts, financials, HR data  | Redact/tokenize unless task requires it    |
    | RESTRICTED | Health, biometric, gov ID, secrets| Never send to 3rd-party model w/o DPA/BAA |
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class TrustLevelEnum(str, Enum):
    """How trusted is a piece of content?

    Used by ContextBlock to determine whether content is "instructions to
    follow" or "data to reason about" (see Section 2B — privilege separation).
    """

    UNTRUSTED = "untrusted"   # Unknown origin, treat as hostile
    LOW = "low"               # Low-trust source (e.g. public web page)
    MEDIUM = "medium"         # Standard user content
    HIGH = "high"             # Authenticated internal source
    CRITICAL = "critical"     # System instructions / admin only
