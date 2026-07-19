"""Tests for RiskTier, HitlMode, ToolDefinition, ToolRegistry, PermissionResult."""

import pytest

from trust_safety.orchestrator.tool_registry import (
    DuplicateToolError,
    HitlMode,
    PermissionResult,
    RiskTier,
    ToolDefinition,
    ToolNotFoundError,
    ToolRegistry,
)


class TestRiskTier:
    """RiskTier enum — maps to HITL modes."""

    def test_values(self):
        assert RiskTier.LOW.value == "low"
        assert RiskTier.MEDIUM.value == "medium"
        assert RiskTier.HIGH.value == "high"
        assert RiskTier.CRITICAL.value == "critical"


class TestHitlMode:
    """HitlMode enum — human-in/on/out-of-the-loop."""

    def test_values(self):
        assert HitlMode.HUMAN_OUT_OF_THE_LOOP.value == "human_out_of_the_loop"
        assert HitlMode.HUMAN_ON_THE_LOOP.value == "human_on_the_loop"
        assert HitlMode.HUMAN_IN_THE_LOOP.value == "human_in_the_loop"


class TestToolDefinition:
    """ToolDefinition — a tool's safety contract."""

    # -- HITL derivation -----------------------------------------------

    def test_low_derives_out_of_loop(self):
        """LOW risk → HUMAN_OUT_OF_THE_LOOP."""
        tool = ToolDefinition(
            name="test_low", description="d", risk_tier=RiskTier.LOW, reversible=True
        )
        assert tool.derive_hitl_mode() == HitlMode.HUMAN_OUT_OF_THE_LOOP

    def test_medium_reversible_derives_on_loop(self):
        """MEDIUM + reversible → HUMAN_ON_THE_LOOP."""
        tool = ToolDefinition(
            name="test_med", description="d", risk_tier=RiskTier.MEDIUM, reversible=True
        )
        assert tool.derive_hitl_mode() == HitlMode.HUMAN_ON_THE_LOOP

    def test_medium_irreversible_derives_in_loop(self):
        """MEDIUM + NOT reversible → HUMAN_IN_THE_LOOP (fail-closed)."""
        tool = ToolDefinition(
            name="test_med_irr", description="d", risk_tier=RiskTier.MEDIUM, reversible=False
        )
        assert tool.derive_hitl_mode() == HitlMode.HUMAN_IN_THE_LOOP

    def test_high_derives_in_loop(self):
        """HIGH risk → HUMAN_IN_THE_LOOP."""
        tool = ToolDefinition(
            name="test_high", description="d", risk_tier=RiskTier.HIGH, reversible=True
        )
        assert tool.derive_hitl_mode() == HitlMode.HUMAN_IN_THE_LOOP

    def test_critical_derives_in_loop(self):
        """CRITICAL risk → HUMAN_IN_THE_LOOP (fail-closed, never autonomous)."""
        tool = ToolDefinition(
            name="test_crit", description="d", risk_tier=RiskTier.CRITICAL, reversible=True
        )
        assert tool.derive_hitl_mode() == HitlMode.HUMAN_IN_THE_LOOP

    # -- Approval derivation -------------------------------------------

    def test_required_approval_derived_high(self):
        """HIGH risk → required_approval = True by default."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.HIGH, reversible=False
        )
        assert tool.required_approval is True

    def test_required_approval_derived_low(self):
        """LOW risk → required_approval = False by default."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.LOW, reversible=True
        )
        assert tool.required_approval is False

    def test_required_approval_explicit_override(self):
        """Explicit required_approval overrides the derivation."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.LOW,
            reversible=True, required_approval=True,
        )
        assert tool.required_approval is True

    # -- Parameter validation ------------------------------------------

    def test_validate_params_valid(self):
        """Valid parameters → no errors."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.LOW,
            parameter_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "count": {"type": "integer"},
                },
                "required": ["path"],
            },
        )
        errors = tool.validate_params({"path": "/tmp/test", "count": 5})
        assert errors == []

    def test_validate_params_missing_required(self):
        """Missing required param → error."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.LOW,
            parameter_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        )
        errors = tool.validate_params({})
        assert len(errors) == 1
        assert "path" in errors[0]

    def test_validate_params_wrong_type(self):
        """Wrong type → error."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.LOW,
            parameter_schema={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
                "required": ["count"],
            },
        )
        errors = tool.validate_params({"count": "not-a-number"})
        assert len(errors) == 1
        assert "count" in errors[0]

    def test_validate_params_no_schema(self):
        """No schema → no validation (but also no errors)."""
        tool = ToolDefinition(
            name="test", description="d", risk_tier=RiskTier.LOW,
        )
        errors = tool.validate_params({"anything": "goes"})
        assert errors == []

    # -- Name validation -----------------------------------------------

    def test_name_pattern(self):
        """Tool name must match ^[a-z][a-z0-9_]*$."""
        with pytest.raises(ValueError):
            ToolDefinition(
                name="BadName", description="d", risk_tier=RiskTier.LOW,
            )


class TestToolRegistry:
    """ToolRegistry — central tool management."""

    def test_register_and_get(self, tool_registry: ToolRegistry):
        """Register a tool and retrieve it."""
        tool = tool_registry.get("read_file")
        assert tool.name == "read_file"
        assert tool.risk_tier == RiskTier.LOW

    def test_register_duplicate_raises(self, tool_registry: ToolRegistry):
        """Registering the same name twice raises DuplicateToolError."""
        dup = ToolDefinition(
            name="read_file", description="dup", risk_tier=RiskTier.LOW,
        )
        with pytest.raises(DuplicateToolError):
            tool_registry.register(dup)

    def test_get_missing_raises(self, tool_registry: ToolRegistry):
        """get() on nonexistent name raises ToolNotFoundError."""
        with pytest.raises(ToolNotFoundError):
            tool_registry.get("nonexistent")

    def test_list_all(self, tool_registry: ToolRegistry):
        """list_all returns all registered tools."""
        tools = tool_registry.list_all()
        assert len(tools) == 4  # read_file, write_file, delete_file, shutdown_system

    def test_list_by_risk(self, tool_registry: ToolRegistry):
        """list_by_risk filters by risk tier."""
        low_tools = tool_registry.list_by_risk(RiskTier.LOW)
        assert len(low_tools) == 1
        assert low_tools[0].name == "read_file"

    def test_check_permission_allowed(self, tool_registry: ToolRegistry):
        """check_permission for allowed role returns allowed=True."""
        result = tool_registry.check_permission("read_file", "viewer")
        assert result.allowed is True
        assert result.hitl_mode == HitlMode.HUMAN_OUT_OF_THE_LOOP

    def test_check_permission_denied(self, tool_registry: ToolRegistry):
        """check_permission for denied role returns allowed=False."""
        result = tool_registry.check_permission("delete_file", "viewer")
        assert result.allowed is False

    def test_check_permission_unknown_tool(self, tool_registry: ToolRegistry):
        """check_permission for unknown tool returns allowed=False."""
        result = tool_registry.check_permission("nonexistent", "admin")
        assert result.allowed is False
        assert "Unknown tool" in result.reason

    def test_get_required_hitl_mode(self, tool_registry: ToolRegistry):
        """get_required_hitl_mode returns correct mode."""
        mode = tool_registry.get_required_hitl_mode("read_file")
        assert mode == HitlMode.HUMAN_OUT_OF_THE_LOOP
        mode2 = tool_registry.get_required_hitl_mode("delete_file")
        assert mode2 == HitlMode.HUMAN_IN_THE_LOOP

    def test_get_required_hitl_mode_missing_raises(self, tool_registry: ToolRegistry):
        """get_required_hitl_mode for unknown tool raises ToolNotFoundError."""
        with pytest.raises(ToolNotFoundError):
            tool_registry.get_required_hitl_mode("does_not_exist")


class TestPermissionResult:
    """PermissionResult — structured outcome of a permission check."""

    def test_allowed_result(self):
        result = PermissionResult(
            allowed=True,
            hitl_mode=HitlMode.HUMAN_OUT_OF_THE_LOOP,
            reason="ok",
            tool_name="read_file",
        )
        assert result.allowed is True

    def test_denied_result(self):
        result = PermissionResult(
            allowed=False,
            reason="Not authorized",
            tool_name="delete_file",
        )
        assert result.allowed is False
        assert result.hitl_mode is None
