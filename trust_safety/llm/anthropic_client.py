"""
Anthropic LLM client — wraps the Anthropic Python SDK.

Also handles DeepSeek's Anthropic-compatible Messages API endpoint
by setting base_url to https://api.deepseek.com/anthropic.

Produces a normalized LLMResponse regardless of which backend serves.
"""

from __future__ import annotations

import time
from typing import Any

from trust_safety.llm.client import LLMClient
from trust_safety.llm.models import LLMConfig, LLMResponse, ToolCall, Usage


class AnthropicLLMClient(LLMClient):
    """Client for Anthropic Messages API (Claude models).

    Works with:
    - api.anthropic.com (native Anthropic)
    - api.deepseek.com/anthropic (DeepSeek's Anthropic-compatible endpoint)

    Fails closed on missing API key — refuses to construct.
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        if not config.api_key:
            raise ValueError(
                "AnthropicLLMClient requires an API key. "
                "Set TS_ANTHROPIC_API_KEY or pass it in config."
            )

        self._client = None  # Lazily initialized

    @property
    def provider_name(self) -> str:
        return "anthropic"

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    async def generate(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> LLMResponse:
        t0 = time.monotonic()

        try:
            client = self._get_client()

            # Build system prompt from the first system message if present
            system = ""
            api_messages: list[dict] = []
            for m in messages:
                if m["role"] == "system":
                    system += m["content"] + "\n"
                else:
                    api_messages.append({"role": m["role"], "content": m["content"]})

            kwargs: dict[str, Any] = {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "messages": api_messages,
            }
            if system.strip():
                kwargs["system"] = system.strip()

            # Convert tools to Anthropic format if provided
            if tools:
                kwargs["tools"] = self._convert_tools(tools)

            response = client.messages.create(**kwargs)

            # Extract text and tool calls
            text = ""
            tool_calls: list[ToolCall] = []
            for block in response.content:
                if block.type == "text":
                    text += block.text
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        name=block.name,
                        params=block.input if isinstance(block.input, dict) else {},
                        call_id=block.id,
                    ))

            return LLMResponse(
                text=text,
                tool_calls=tool_calls,
                stop_reason=response.stop_reason or "end_turn",
                usage=Usage(
                    input_tokens=response.usage.input_tokens if response.usage else 0,
                    output_tokens=response.usage.output_tokens if response.usage else 0,
                ),
                latency_ms=(time.monotonic() - t0) * 1000,
                provider_name="anthropic",
                model_name=self.config.model,
            )

        except Exception as exc:
            # Check for common failure modes
            error_msg = str(exc).lower()
            if "401" in error_msg or "unauthorized" in error_msg:
                raise RuntimeError(f"Anthropic auth failed: {exc}") from exc
            if "429" in error_msg or "rate" in error_msg:
                raise RuntimeError(f"Anthropic rate limited: {exc}") from exc
            if "timeout" in error_msg:
                raise TimeoutError(f"Anthropic timeout: {exc}") from exc
            raise

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazy-init the Anthropic client on first call."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required. Install with: "
                    "pip install anthropic"
                )
            client_kwargs: dict = {"api_key": self.config.api_key}
            if self.config.base_url:
                client_kwargs["base_url"] = self.config.base_url
            self._client = anthropic.Anthropic(**client_kwargs)
        return self._client

    @staticmethod
    def _convert_tools(tools: list[dict]) -> list[dict]:
        """Convert provider-agnostic tool format to Anthropic format.

        Input:  [{"name": "read_file", "description": "...", "input_schema": {...}}]
        Output: [{"name": "read_file", "description": "...", "input_schema": {...}}]
        (They're the same — Anthropic uses the same format already.)
        """
        return tools
