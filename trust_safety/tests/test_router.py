"""Tests for ProviderRouter — routing policy selection."""

import pytest

from trust_safety.llm.mock_client import MockLLMClient
from trust_safety.llm.models import LLMConfig
from trust_safety.llm.router import ProviderRouter, RoutingPolicy


class TestProviderRouter:
    """Provider selection based on routing policy."""

    def test_fixed_default_routes_to_primary(self):
        primary = MockLLMClient(LLMConfig(provider="mock", model="primary"))
        router = ProviderRouter(primary=primary, policy=RoutingPolicy.FIXED_DEFAULT, default_provider="mock")
        client = router.route()
        assert client.provider_name == "mock"

    def test_fallback_only_returns_primary(self):
        primary = MockLLMClient(LLMConfig(provider="mock", model="main"))
        secondary = MockLLMClient(LLMConfig(provider="mock", model="backup"))
        router = ProviderRouter(
            primary=primary, secondary=secondary,
            policy=RoutingPolicy.FALLBACK_ONLY, default_provider="mock",
        )
        assert router.route().config.model == "main"

    def test_list_clients(self):
        primary = MockLLMClient(LLMConfig(provider="mock", model="a"))
        secondary = MockLLMClient(LLMConfig(provider="mock", model="b"))
        router = ProviderRouter(primary=primary, secondary=secondary, default_provider="mock")
        clients = router.list_clients()
        assert len(clients) == 2

    def test_list_clients_no_secondary(self):
        primary = MockLLMClient()
        router = ProviderRouter(primary=primary, default_provider="mock")
        assert len(router.list_clients()) == 1

    def test_task_based_routing(self):
        primary = MockLLMClient(LLMConfig(provider="mock", model="powerful"))
        secondary = MockLLMClient(LLMConfig(provider="mock", model="cheap"))
        router = ProviderRouter(
            primary=primary, secondary=secondary,
            policy=RoutingPolicy.TASK_BASED, default_provider="mock",
        )
        assert router.route(task_type="code").config.model == "powerful"
        assert router.route(task_type="chat").config.model == "cheap"
