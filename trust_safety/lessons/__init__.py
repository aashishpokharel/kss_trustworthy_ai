"""
trust_safety.lessons - stdlib-only teaching layer
=================================================

This subpackage is what the KSS session lessons import. It exposes the
minimal, auditable, dependency-free version of the safety primitives that
``trust_safety`` implements in production form elsewhere in the package.

Why a separate subpackage?
--------------------------
The production guardrail stack (``trust_safety.guardrails``,
``trust_safety.orchestrator``, ``trust_safety.governance``) depends on
Pydantic v2 and Microsoft Presidio and requires Python >= 3.10. The session
teaches the same ideas in a form that runs anywhere on the standard library
alone, so students can read the code end-to-end and run every demo without
installing anything.

Everything here is the *teaching view* of a richer production module. See
the module docstrings in :mod:`trust_safety.lessons.safety` and
:mod:`trust_safety.lessons.config` for the exact class-by-class mapping.

Public API
----------
    >>> from trust_safety.lessons.safety import ContentFilter
    >>> from trust_safety.lessons.config import TrustworthyConfig, TrustLevel
    >>> from trust_safety.lessons import ContentFilter, TrustworthyConfig
"""

from trust_safety.lessons.config import TrustLevel, TrustworthyConfig
from trust_safety.lessons.safety import (
    AuditEntry,
    AuditLogger,
    ContentFilter,
    OutputValidator,
    PromptInjectionDetector,
    ValidationResult,
    compute_hash,
    mask_sensitive,
)

__all__ = [
    "ContentFilter",
    "PromptInjectionDetector",
    "OutputValidator",
    "ValidationResult",
    "AuditLogger",
    "AuditEntry",
    "mask_sensitive",
    "compute_hash",
    "TrustLevel",
    "TrustworthyConfig",
]
