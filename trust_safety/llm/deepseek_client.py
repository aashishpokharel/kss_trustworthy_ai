"""
DeepSeek LLM client — wraps the OpenAI Python SDK pointed at DeepSeek's API.

DeepSeek offers an OpenAI-compatible chat/completions endpoint at
https://api.deepseek.com/v1.  This client speaks that format and
normalizes responses into the shared LLMResponse schema.
"""

from __future__ import annotations

import time
from typing import Any

from trust_safety.llm.client import LLMClient
from trust_safety.llm.models import LLMConfig, LLMResponse, ToolCall, Usage


class DeepSeekLLMClient(LLMClient):
    """Client for DeepSeek's OpenAI-compatible chat/completions API.

    Fails closed on missing API key.
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        if not config.api_key:
            raise ValueError(
                "DeepSeekLLMClient requires an API key. "
                "Set TS_DEEPSEEK_API_KEY or pass it in config."
            )
        self._client = None

    @property
    def provider_name(self) -> str:
        return "deepseek"

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

            kwargs: dict[str, Any] = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            if tools:
                kwargs["tools"] = self._convert_tools_to_openai(tools)

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            msg = choice.message

            # Extract text and tool calls
            text = msg.content or ""
            tool_calls: list[ToolCall] = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    import json as _json
                    try:
                        params = _json.loads(tc.function.arguments)
                    except Exception:
                        params = {}
                    tool_calls.append(ToolCall(
                        name=tc.function.name,
                        params=params,
                        call_id=tc.id,
                    ))

            return LLMResponse(
                text=text,
                tool_calls=tool_calls,
                stop_reason=choice.finish_reason or "end_turn",
                usage=Usage(
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                ),
                latency_ms=(time.monotonic() - t0) * 1000,
                provider_name="deepseek",
                model_name=self.config.model,
            )

        except Exception as exc:
            error_msg = str(exc).lower()
            if "401" in error_msg or "unauthorized" in error_msg:
                raise RuntimeError(f"DeepSeek auth failed: {exc}") from exc
            if "429" in error_msg or "rate" in error_msg:
                raise RuntimeError(f"DeepSeek rate limited: {exc}") from exc
            if "timeout" in error_msg:
                raise TimeoutError(f"DeepSeek timeout: {exc}") from exc
            raise

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazy-init the OpenAI client pointed at DeepSeek."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai package is required for DeepSeek client. "
                    "Install with: pip install openai"
                )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://api.deepseek.com/v1",
            )
        return self._client

    @staticmethod
    def _convert_tools_to_openai(tools: list[dict]) -> list[dict]:
        """Convert provider-agnostic tools to OpenAI function format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return openai_tools
