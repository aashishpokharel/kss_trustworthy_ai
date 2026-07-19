"""Mock LLM client — deterministic, used in tests and CI."""

from __future__ import annotations

import re
import time
from typing import Callable

from trust_safety.llm.client import LLMClient
from trust_safety.llm.models import LLMConfig, LLMResponse, ToolCall, Usage


class MockLLMClient(LLMClient):
    """Deterministic LLM client for testing.

    Usage::

        mock = MockLLMClient(LLMConfig(provider="mock"))
        mock.add_response("capital of France", "The capital of France is Paris.")
        mock.add_response("delete.*file", tool_call=ToolCall(name="delete_file", params={"path": "/tmp/x"}))
        resp = await mock.generate([{"role": "user", "content": "What is the capital of France?"}])
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        super().__init__(config or LLMConfig(provider="mock", model="mock-model"))
        self._responses: list[tuple[str, str | ToolCall]] = []
        self._default_response = "This is a mock response."
        self._call_count = 0
        self._on_generate: Callable | None = None

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def call_count(self) -> int:
        return self._call_count

    # ------------------------------------------------------------------
    # Response registration
    # ------------------------------------------------------------------

    def add_response(self, pattern: str, text: str = "", tool_call: ToolCall | None = None) -> None:
        """Register a canned response.  First matching pattern wins."""
        if tool_call:
            self._responses.append((pattern, tool_call))
        else:
            self._responses.append((pattern, text))

    def set_default(self, text: str) -> None:
        """Set the fallback response when no pattern matches."""
        self._default_response = text

    def on_generate(self, callback: Callable) -> None:
        """Register a callback invoked on every generate() call.

        Useful for test assertions::

            calls = []
            mock.on_generate(lambda msgs, tools: calls.append(msgs))
        """
        self._on_generate = callback

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    async def generate(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> LLMResponse:
        self._call_count += 1
        t0 = time.monotonic()

        if self._on_generate:
            self._on_generate(messages, tools)

        # Extract user text for pattern matching
        user_text = ""
        for m in messages:
            if m.get("role") == "user":
                user_text += m.get("content", "") + " "

        # Check registered patterns
        for pattern, response in self._responses:
            if re.search(pattern, user_text, re.IGNORECASE):
                if isinstance(response, ToolCall):
                    return LLMResponse(
                        text="",
                        tool_calls=[response],
                        stop_reason="tool_use",
                        usage=Usage(input_tokens=len(user_text) // 4, output_tokens=30),
                        latency_ms=(time.monotonic() - t0) * 1000,
                        provider_name="mock",
                        model_name=self.config.model,
                    )
                return LLMResponse(
                    text=response,
                    stop_reason="end_turn",
                    usage=Usage(input_tokens=len(user_text) // 4, output_tokens=len(response) // 4),
                    latency_ms=(time.monotonic() - t0) * 1000,
                    provider_name="mock",
                    model_name=self.config.model,
                )

        # Fallback
        return LLMResponse(
            text=self._default_response,
            stop_reason="end_turn",
            usage=Usage(input_tokens=len(user_text) // 4, output_tokens=len(self._default_response) // 4),
            latency_ms=(time.monotonic() - t0) * 1000,
            provider_name="mock",
            model_name=self.config.model,
        )
