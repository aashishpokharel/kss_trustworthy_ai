"""
Provider Router — selects which LLMClient handles a given request.

Routing policies (per llm-integration-architecture.md §2.1):
- fixed_default  — always use the configured default provider
- task_based     — route based on task type (code → anthropic, chat → deepseek)
- cost_based     — route to the cheapest provider that meets quality floor
- fallback_only  — use primary; fallback to secondary only if primary fails
"""

from __future__ import annotations

from enum import Enum

from trust_safety.llm.client import LLMClient
from trust_safety.llm.models import LLMConfig


class RoutingPolicy(str, Enum):
    FIXED_DEFAULT = "fixed_default"
    TASK_BASED = "task_based"
    COST_BASED = "cost_based"
    FALLBACK_ONLY = "fallback_only"


class ProviderRouter:
    """Select an LLM provider per request based on configured policy.

    Usage::

        router = ProviderRouter(
            primary=anthropic_client,
            secondary=deepseek_client,
            policy=RoutingPolicy.FIXED_DEFAULT,
            default_provider="anthropic",
        )
        client = router.route()
        response = await client.generate(messages)
    """

    def __init__(
        self,
        primary: LLMClient,
        secondary: LLMClient | None = None,
        policy: RoutingPolicy = RoutingPolicy.FIXED_DEFAULT,
        default_provider: str = "anthropic",
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.policy = policy
        self.default_provider = default_provider

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def route(self, task_type: str | None = None) -> LLMClient:
        """Select the client for this request.

        Args:
            task_type: Optional task hint for task_based routing.

        Returns:
            The selected LLMClient.
        """
        if self.policy == RoutingPolicy.FIXED_DEFAULT:
            return self._by_name(self.default_provider)

        if self.policy == RoutingPolicy.TASK_BASED:
            if task_type in ("code", "analysis", "reasoning"):
                # Route complex tasks to the primary (usually more capable)
                return self.primary
            # Route conversational/simple tasks to secondary
            return self.secondary or self.primary

        if self.policy == RoutingPolicy.COST_BASED:
            # Simplified: prefer secondary if available (assumed cheaper)
            return self.secondary or self.primary

        if self.policy == RoutingPolicy.FALLBACK_ONLY:
            return self.primary

        return self.primary

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _by_name(self, name: str) -> LLMClient:
        """Get client by provider name."""
        if self.secondary and self.secondary.provider_name == name:
            return self.secondary
        return self.primary

    def list_clients(self) -> list[LLMClient]:
        """Return all registered clients."""
        clients = [self.primary]
        if self.secondary:
            clients.append(self.secondary)
        return clients
