"""Tests for Settings configuration."""

import os
from pathlib import Path

import pytest

from trust_safety.config import Environment, Settings, get_settings


class TestEnvironment:
    """Environment enum."""

    def test_values(self):
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.PRODUCTION.value == "production"


class TestSettings:
    """Settings — env-based config with validation."""

    def test_default_values(self):
        """Defaults are sensible for local dev."""
        settings = Settings()
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.audit_log_path == Path("./data/audit_log.jsonl")
        assert settings.hitl_timeout_seconds == 300
        assert settings.hitl_fail_closed is True
        assert settings.policy_profiles == ["none"]

    def test_env_prefix_ts(self, monkeypatch):
        """TS_ prefixed env vars override defaults."""
        monkeypatch.setenv("TS_ENVIRONMENT", "production")
        monkeypatch.setenv("TS_HITL_TIMEOUT_SECONDS", "600")
        settings = Settings()
        assert settings.environment == Environment.PRODUCTION
        assert settings.hitl_timeout_seconds == 600

    def test_validate_rules_valid_dev(self):
        """Valid dev config returns empty issues."""
        settings = Settings(environment=Environment.DEVELOPMENT)
        issues = settings.validate_rules()
        assert issues == []

    def test_validate_rules_valid_testing(self):
        """Valid testing config returns empty issues."""
        settings = Settings(environment=Environment.TESTING)
        issues = settings.validate_rules()
        assert issues == []

    def test_validate_rules_unknown_profile(self):
        """Unknown compliance profile → validation issue."""
        settings = Settings(policy_profiles=["made_up_profile"])
        issues = settings.validate_rules()
        assert len(issues) == 1
        assert "Unknown compliance profile" in issues[0]

    def test_validate_rules_production_timeout_warning(self):
        """Excessive HITL timeout in production → issue flagged."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            hitl_timeout_seconds=7200,  # 2 hours
        )
        issues = settings.validate_rules()
        assert any("timeout" in i.lower() for i in issues)

    def test_validate_rules_production_fail_open_critical(self):
        """hitl_fail_closed=False in production → CRITICAL issue."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            hitl_fail_closed=False,
        )
        issues = settings.validate_rules()
        assert any("CRITICAL" in i for i in issues)

    def test_get_settings_singleton(self):
        """get_settings returns the same instance each call."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_field_validation(self):
        """Out-of-range values are rejected by Pydantic."""
        with pytest.raises(ValueError):
            Settings(hitl_timeout_seconds=10)  # Below min of 30
