"""
Trustworthy AI Configuration (teaching layer)
============================================

Standard-library-only configuration template used throughout the KSS
session lessons. Demonstrates configuration best practices for LLM
applications: no hardcoded secrets, validated settings, explicit safety
controls, and a single ``TrustLevel`` knob that scales the guardrails.

This module is the *pedagogical* counterpart of the production
configuration layer:

    Teaching (this module)          Production (trust_safety)
    ------------------------------  -------------------------------------------
    ``TrustworthyConfig``           ``config.Settings`` (pydantic-settings,
                                    env-driven, validated via ``validate_rules``)
    ``TrustLevel``                  ``config.Settings.trust_level`` plus the
                                    compliance profiles in ``policies.defaults``
                                    (``ComplianceProfile`` / ``GDPR_PROFILE`` ...)
    ``TrustworthyConfig.validate``  ``config.Settings.validate_rules``

The production equivalents require Python >= 3.10 plus the packages listed
in ``trust_safety/requirements.txt``. This teaching template deliberately
does not; it is the version the lessons exercise.
"""
import os
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class TrustLevel(Enum):
    """Trust levels for AI operations"""
    STRICT = "strict"       # Maximum safety, reject uncertain
    BALANCED = "balanced"   # Standard safety with some flexibility
    FLEXIBLE = "flexible"   # Allow more autonomy but log concerns


@dataclass
class TrustworthyConfig:
    """
    Configuration template for trustworthy AI.
    
    === USUAL WAY (Anti-pattern) ===
    config = {
        "api_key": "sk-xxx",  # Hardcoded!
        "model": "gpt-4",
        "temperature": 0.7,   # No thought about safety
        "max_tokens": 2000
    }
    
    === TRUSTWORTHY WAY ===
    Uses env vars, strict typing, and safety controls
    """
    
    # Authentication (never hardcode)
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    
    # Model selection with constraints
    allowed_models: List[str] = field(default_factory=lambda: [
        "gpt-4", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet"
    ])
    model: str = "gpt-4"
    
    # Safety controls
    trust_level: TrustLevel = TrustLevel.BALANCED
    max_tokens: int = 1024
    temperature: float = 0.2  # Lower = more deterministic, safer
    top_p: float = 0.9
    
    # Content filtering
    enable_content_filter: bool = True
    enable_prompt_injection_detection: bool = True
    enable_output_validation: bool = True
    
    # Rate limiting and monitoring
    max_requests_per_minute: int = 60
    enable_audit_logging: bool = True
    enable_cost_tracking: bool = True
    
    # Guardrails
    sensitive_topic_list: List[str] = field(default_factory=lambda: [
        "medical_advice", "legal_advice", "financial_investment",
        "personal_identifiable_information"
    ])
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        if not self.api_key:
            issues.append("Missing API key - use environment variable LLM_API_KEY")
        if self.model not in self.allowed_models:
            issues.append(f"Model {self.model} not in allowed list: {self.allowed_models}")
        if self.temperature > 1.0:
            issues.append("Temperature > 1.0 reduces determinism significantly")
        if self.max_tokens > 4096:
            issues.append("max_tokens > 4096 may lead to excessive generation")
        return issues