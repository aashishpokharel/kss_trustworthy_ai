"""
Tool Registry — the source of truth for every tool the agent can call.

Every tool declares its risk tier, reversibility, and parameter schema at
registration time.  The registry derives the required HITL mode automatically
(Section 9.2 — human-in/on/out-of-the-loop).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ------------------------------------------------------------------
# Risk & HITL enums
# ------------------------------------------------------------------

class RiskTier(str, Enum):
    """Tool risk classification — maps directly to HITL mode (Section 9.2).

    LOW      — fully autonomous (human-out-of-the-loop)
    MEDIUM   — auto-execute, human can interrupt (on-the-loop)
    HIGH     — human must approve before execution (in-the-loop)
    CRITICAL — human-in-the-loop + secondary approval or circuit-breaker
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HitlMode(str, Enum):
    """Human-in-the-loop modes from Section 9.2."""

    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    HUMAN_ON_THE_LOOP = "human_on_the_loop"
    HUMAN_OUT_OF_THE_LOOP = "human_out_of_the_loop"


# ------------------------------------------------------------------
# Tool Definition
# ------------------------------------------------------------------

class ToolDefinition(BaseModel):
    """A capability the agent can invoke, with its safety contract.

    The safety contract includes:
    * Risk tier → derived HITL mode
    * Reversibility flag — irreversible actions get stricter HITL
    * Parameter JSON Schema — validated before every invocation
    * Role-based access — who can call this tool
    * Rate limiting — max calls per minute
    """

    name: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique tool identifier.  Lowercase snake_case.",
    )
    description: str = Field(
        ..., description="Human-readable description of what this tool does."
    )
    risk_tier: RiskTier = Field(
        ..., description="Risk classification.  Drives HITL mode derivation."
    )
    reversible: bool = Field(
        default=False,
        description="Can the action be undone?  Irreversible actions get "
                    "stricter HITL treatment.",
    )
    required_approval: bool | None = Field(
        default=None,
        description="Override for HITL derivation.  None = auto-derive from "
                    "risk_tier + reversible.",
    )
    parameter_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for parameters.  Validated before every call.",
    )
    rate_limit_per_minute: int = Field(
        default=60, ge=1, description="Maximum invocations per minute."
    )
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Execution timeout."
    )
    allowed_roles: list[str] = Field(
        default_factory=lambda: ["admin"],
        description="User roles permitted to invoke this tool.",
    )

    @model_validator(mode="after")
    def _set_approval_default(self) -> "ToolDefinition":
        """If required_approval was not set, derive it from risk_tier."""
        if self.required_approval is None:
            self.required_approval = self.risk_tier in (
                RiskTier.HIGH,
                RiskTier.CRITICAL,
            )
        return self

    # --------------------------------------------------------------
    # HITL derivation (Section 9.2)
    # --------------------------------------------------------------

    def derive_hitl_mode(self) -> HitlMode:
        """Map risk_tier + reversible → HITL mode.

        =========  ========================
        Risk Tier  HITL Mode
        =========  ========================
        LOW        HUMAN_OUT_OF_THE_LOOP
        MEDIUM     ON-the-loop if reversible, otherwise IN-the-loop
        HIGH       HUMAN_IN_THE_LOOP
        CRITICAL   HUMAN_IN_THE_LOOP (fail-closed)
        =========  ========================
        """
        if self.risk_tier == RiskTier.LOW:
            return HitlMode.HUMAN_OUT_OF_THE_LOOP
        if self.risk_tier == RiskTier.MEDIUM:
            if self.reversible:
                return HitlMode.HUMAN_ON_THE_LOOP
            return HitlMode.HUMAN_IN_THE_LOOP
        # HIGH and CRITICAL → always in-the-loop
        return HitlMode.HUMAN_IN_THE_LOOP

    # --------------------------------------------------------------
    # Parameter validation
    # --------------------------------------------------------------

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate *params* against ``parameter_schema`` using JSON Schema.

        Returns a list of human-readable validation errors (empty = valid).
        """
        errors: list[str] = []

        schema = self.parameter_schema
        if not schema:
            return errors  # No schema = no validation

        required: list[str] = schema.get("required", [])
        properties: dict[str, Any] = schema.get("properties", {})

        # Check required fields are present
        for field in required:
            if field not in params:
                errors.append(f"Missing required parameter: '{field}'")

        # Check types for provided fields
        for field, value in params.items():
            if field not in properties:
                continue  # Unknown fields are silently allowed (forward compat)

            prop = properties[field]
            expected_type = prop.get("type", "string")

            if expected_type == "string" and not isinstance(value, str):
                errors.append(
                    f"Parameter '{field}': expected str, got {type(value).__name__}"
                )
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(
                    f"Parameter '{field}': expected int, got {type(value).__name__}"
                )
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(
                    f"Parameter '{field}': expected number, got {type(value).__name__}"
                )
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(
                    f"Parameter '{field}': expected bool, got {type(value).__name__}"
                )

        return errors


# ------------------------------------------------------------------
# Permission result
# ------------------------------------------------------------------

class PermissionResult(BaseModel):
    """The outcome of a permission check."""

    allowed: bool
    hitl_mode: HitlMode | None = Field(
        default=None, description="Required HITL mode if allowed."
    )
    reason: str = Field(default="", description="Human-readable explanation.")
    tool_name: str = Field(..., description="The tool this result is for.")


# ------------------------------------------------------------------
# Custom exceptions
# ------------------------------------------------------------------

class DuplicateToolError(ValueError):
    """Raised when registering a tool name that already exists."""


class ToolNotFoundError(ValueError):
    """Raised when looking up a tool that was never registered."""


# ------------------------------------------------------------------
# Tool Registry
# ------------------------------------------------------------------

class ToolRegistry(BaseModel):
    """Central registry of all tools the agent can invoke.

    This is the source of truth for:
    * What tools exist
    * Their risk posture
    * Who can call them
    * What HITL mode is required
    """

    _tools: dict[str, ToolDefinition] = {}

    # -- Registration -------------------------------------------------

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool.  Raises DuplicateToolError on name collision."""
        if tool.name in self._tools:
            raise DuplicateToolError(
                f"Tool '{tool.name}' is already registered."
            )
        self._tools[tool.name] = tool

    # -- Lookup -------------------------------------------------------

    def get(self, name: str) -> ToolDefinition:
        """Look up a tool by name.  Raises ToolNotFoundError if missing."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    # -- Listing ------------------------------------------------------

    def list_all(self) -> list[ToolDefinition]:
        """Return every registered tool."""
        return list(self._tools.values())

    def list_by_risk(self, tier: RiskTier) -> list[ToolDefinition]:
        """Return tools registered at a specific risk tier."""
        return [t for t in self._tools.values() if t.risk_tier == tier]

    # -- Permission ---------------------------------------------------

    def check_permission(self, tool_name: str, role: str) -> PermissionResult:
        """Check whether *role* is allowed to invoke *tool_name*.

        Returns a structured PermissionResult with the required HITL mode.
        """
        try:
            tool = self.get(tool_name)
        except ToolNotFoundError:
            return PermissionResult(
                allowed=False,
                reason=f"Unknown tool: '{tool_name}'",
                tool_name=tool_name,
            )

        if role not in tool.allowed_roles and "admin" not in [role]:
            # admin always has access — shortcut
            if role not in tool.allowed_roles:
                return PermissionResult(
                    allowed=False,
                    reason=(
                        f"Role '{role}' is not permitted to use '{tool_name}'. "
                        f"Allowed roles: {tool.allowed_roles}"
                    ),
                    tool_name=tool_name,
                )

        hitl_mode = tool.derive_hitl_mode()
        return PermissionResult(
            allowed=True,
            hitl_mode=hitl_mode,
            reason=f"Access granted at {hitl_mode.value}",
            tool_name=tool_name,
        )

    def get_required_hitl_mode(self, tool_name: str) -> HitlMode:
        """Return the HITL mode required for *tool_name*."""
        tool = self.get(tool_name)
        return tool.derive_hitl_mode()
