"""Abstract base class for all LLM provider clients."""

from __future__ import annotations

from abc import ABC, abstractmethod

from trust_safety.llm.models import LLMConfig, LLMResponse
from trust_safety.models.context import ContextBlock


class LLMClient(ABC):
    """Interface every LLM provider must implement.

    Guardrail code, the orchestrator, and tests all depend on this
    interface — never on a vendor SDK directly.
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Send a request to the LLM and return a normalized response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions in provider-agnostic format.
            stream: If True, stream tokens (not fully supported yet).

        Returns:
            LLMResponse with text, tool_calls, usage, latency, provider info.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
        ...

    async def health_check(self) -> bool:
        """Quick connectivity test.  Default: attempt a minimal generate call."""
        try:
            resp = await self.generate(
                [{"role": "user", "content": "Hi"}],
                tools=None,
            )
            return bool(resp.text)
        except Exception:
            return False
