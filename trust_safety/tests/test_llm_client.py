"""Tests for LLM clients — interface conformance for all implementations."""

import pytest

from trust_safety.llm.client import LLMClient
from trust_safety.llm.models import LLMConfig, ToolCall
from trust_safety.llm.mock_client import MockLLMClient


class TestMockLLMClient:
    """MockLLMClient — deterministic, used in all other tests."""

    @pytest.mark.asyncio
    async def test_generate_returns_response(self):
        client = MockLLMClient()
        resp = await client.generate([{"role": "user", "content": "Hello"}])
        assert resp.text
        assert resp.provider_name == "mock"
        assert resp.stop_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_pattern_matching(self):
        client = MockLLMClient()
        client.add_response("capital of France", "The capital is Paris.")
        client.add_response("capital of Germany", "The capital is Berlin.")
        resp = await client.generate([{"role": "user", "content": "What is the capital of France?"}])
        assert "Paris" in resp.text

    @pytest.mark.asyncio
    async def test_fallback_default(self):
        client = MockLLMClient()
        client.set_default("I don't know.")
        resp = await client.generate([{"role": "user", "content": "Some obscure question"}])
        assert resp.text == "I don't know."

    @pytest.mark.asyncio
    async def test_tool_call_response(self):
        client = MockLLMClient()
        client.add_response("delete", tool_call=ToolCall(
            name="delete_file", params={"path": "/tmp/x"}, reasoning="User requested deletion",
        ))
        resp = await client.generate([{"role": "user", "content": "delete the temp file"}])
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "delete_file"
        assert resp.stop_reason == "tool_use"

    @pytest.mark.asyncio
    async def test_call_count(self):
        client = MockLLMClient()
        assert client.call_count == 0
        await client.generate([{"role": "user", "content": "a"}])
        await client.generate([{"role": "user", "content": "b"}])
        assert client.call_count == 2

    @pytest.mark.asyncio
    async def test_on_generate_callback(self):
        client = MockLLMClient()
        calls = []
        client.on_generate(lambda msgs, tools: calls.append(msgs))
        await client.generate([{"role": "user", "content": "test"}])
        assert len(calls) == 1
        assert calls[0][0]["content"] == "test"

    @pytest.mark.asyncio
    async def test_health_check(self):
        client = MockLLMClient()
        healthy = await client.health_check()
        assert healthy


class TestLLMConfig:
    """LLMConfig validation."""

    def test_defaults(self):
        config = LLMConfig()
        assert config.provider == "mock"
        assert not config.is_configured  # No API key

    def test_configured_with_key(self):
        config = LLMConfig(api_key="sk-test", model="claude-sonnet-5")
        assert config.is_configured

    def test_missing_key_not_configured(self):
        config = LLMConfig(model="claude-sonnet-5")
        assert not config.is_configured

    def test_missing_api_key_raises_on_real_client(self):
        """Anthropic client requires API key — fails closed."""
        from trust_safety.llm.anthropic_client import AnthropicLLMClient
        with pytest.raises(ValueError, match="API key"):
            AnthropicLLMClient(LLMConfig(provider="anthropic", model="claude-sonnet-5"))
