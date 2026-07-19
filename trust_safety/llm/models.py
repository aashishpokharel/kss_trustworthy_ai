"""Shared data models for the LLM provider abstraction layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A tool invocation extracted from the LLM response."""
    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    reasoning: str | None = Field(
        default=None,
        description="The model's stated reasoning/plan before this call "
                    "(Section 9.1 — reasoning-vs-action divergence check).",
    )
    call_id: str | None = None


class Usage(BaseModel):
    """Token usage for a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0


class LLMResponse(BaseModel):
    """Normalized response from any LLM provider.

    Every client implementation (mock, Anthropic, DeepSeek) must
    produce this same shape so guardrail code never depends on
    provider-specific response fields.
    """
    text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    stop_reason: str = "end_turn"  # end_turn, max_tokens, tool_use, stop_sequence, refusal
    usage: Usage = Field(default_factory=Usage)
    latency_ms: float = 0.0
    provider_name: str = "unknown"
    model_name: str = "unknown"
    request_id: str | None = None


class LLMConfig(BaseModel):
    """Configuration for a single LLM provider.

    One instance per provider.  Read from environment or config file;
    never hardcode API keys.
    """
    provider: str = "mock"
    model: str = "claude-sonnet-5"
    base_url: str = ""
    api_key: str = ""
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    timeout_seconds: int = Field(default=60, ge=5, le=600)
    max_retries: int = Field(default=3, ge=0, le=10)
    cost_ceiling_daily_usd: float = Field(default=50.0, ge=0.0)
    zero_retention_enabled: bool = Field(
        default=False,
        description="Has the provider confirmed zero-retention/no-train "
                    "for our account?  Must be True before RESTRICTED-tier "
                    "data is routed to this provider."
    )

    @property
    def is_configured(self) -> bool:
        """Does this provider have the minimum config to attempt a call?"""
        return bool(self.api_key) and bool(self.model)
