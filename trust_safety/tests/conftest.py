"""Shared pytest fixtures for Phase 0 tests."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from trust_safety.config import Environment, Settings
from trust_safety.governance.audit_log.store import (
    AppendOnlyFileStore,
    AuditLogger,
)
from trust_safety.main import app
from trust_safety.models.base import DataTier, TrustLevelEnum
from trust_safety.models.context import ContextBlock, ProvenanceTag
from trust_safety.orchestrator.tool_registry import (
    RiskTier,
    ToolDefinition,
    ToolRegistry,
)
from trust_safety.policies.registry import PolicyRegistry


# ------------------------------------------------------------------
# Audit log fixtures
# ------------------------------------------------------------------

@pytest.fixture
def tmp_audit_log_path(tmp_path: Path) -> Path:
    """Temporary audit log file path."""
    return tmp_path / "audit.jsonl"


@pytest.fixture
def audit_store(tmp_audit_log_path: Path) -> AppendOnlyFileStore:
    """Fresh AppendOnlyFileStore pointed at a temp file."""
    return AppendOnlyFileStore(tmp_audit_log_path)


@pytest.fixture
def audit_logger(audit_store: AppendOnlyFileStore) -> AuditLogger:
    """AuditLogger wrapping a temp store."""
    return AuditLogger(audit_store)


# ------------------------------------------------------------------
# Tool registry fixtures
# ------------------------------------------------------------------

@pytest.fixture
def tool_registry() -> ToolRegistry:
    """ToolRegistry pre-seeded with sample tools."""
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="read_file",
        description="Read a file.",
        risk_tier=RiskTier.LOW,
        reversible=True,
        allowed_roles=["admin", "developer", "viewer"],
        parameter_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    ))
    registry.register(ToolDefinition(
        name="write_file",
        description="Write to a file.",
        risk_tier=RiskTier.MEDIUM,
        reversible=True,
        allowed_roles=["admin", "developer"],
        parameter_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    ))
    registry.register(ToolDefinition(
        name="delete_file",
        description="Delete a file.",
        risk_tier=RiskTier.HIGH,
        reversible=False,
        allowed_roles=["admin"],
        parameter_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    ))
    registry.register(ToolDefinition(
        name="shutdown_system",
        description="Shut down the system.",
        risk_tier=RiskTier.CRITICAL,
        reversible=False,
        allowed_roles=["admin"],
        rate_limit_per_minute=1,
    ))
    return registry


# ------------------------------------------------------------------
# Policy registry fixtures
# ------------------------------------------------------------------

@pytest.fixture
def policy_registry() -> PolicyRegistry:
    """Fresh PolicyRegistry with built-in profiles."""
    return PolicyRegistry()


# ------------------------------------------------------------------
# Context / provenance fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_provenance_tag() -> ProvenanceTag:
    """A typical provenance tag."""
    return ProvenanceTag(
        source_id="user-123",
        source_type="user_input",
        origin="human_input",
        data_tier=DataTier.INTERNAL,
    )


@pytest.fixture
def sample_context_block(sample_provenance_tag: ProvenanceTag) -> ContextBlock:
    """A typical untrusted context block."""
    return ContextBlock(
        content="What is the weather today?",
        source="end-user chat",
        trust_level=TrustLevelEnum.UNTRUSTED,
        provenance=sample_provenance_tag,
    )


# ------------------------------------------------------------------
# Settings fixtures
# ------------------------------------------------------------------

@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings overridden for testing."""
    return Settings(
        environment=Environment.TESTING,
        audit_log_path=tmp_path / "test_audit.jsonl",
        policy_profiles=["none"],
    )


# ------------------------------------------------------------------
# FastAPI test client
# ------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient for the trust-safety app."""
    return TestClient(app)


# ------------------------------------------------------------------
# Golden set paths
# ------------------------------------------------------------------

@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"
