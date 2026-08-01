"""
Provider Manager for caching, instantiating, and orchestrating AI providers.
"""

import logging
from typing import Dict

from app.config.settings import settings
from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderConfigurationError, ProviderNotFoundError
from app.providers.registry import provider_registry

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages instantiation, caching, configuration detection, and failover strategy of providers.
    """

    def __init__(self) -> None:
        self._instances: Dict[str, BaseProvider] = {}
        # Default priority order for failovers
        self.priority_order = ["groq", "gemini", "openrouter", "openai", "anthropic", "ollama"]

    def is_configured(self, name: str) -> bool:
        """
        Check if the required API keys or URLs exist for the provider.
        """
        name_lower = name.lower()
        if name_lower == "groq":
            return bool(settings.GROQ_API_KEY)
        if name_lower == "gemini":
            return bool(settings.GEMINI_API_KEY)
        if name_lower == "openai":
            return bool(settings.OPENAI_API_KEY)
        if name_lower == "anthropic":
            return bool(settings.ANTHROPIC_API_KEY)
        if name_lower == "openrouter":
            return bool(settings.OPENROUTER_API_KEY)
        if name_lower == "ollama":
            return bool(settings.OLLAMA_BASE_URL)
        return False

    def get_provider(self, name: str) -> BaseProvider:
        """
        Retrieve cached singleton instance or instantiate class if configured.
        """
        name_lower = name.lower()
        if not provider_registry.exists(name_lower):
            raise ProviderNotFoundError(f"AI Provider '{name}' is not registered.")

        if not self.is_configured(name_lower):
            raise ProviderConfigurationError(f"AI Provider '{name}' is not configured (missing credentials).")

        if name_lower not in self._instances:
            logger.info(f"Instantiating and caching provider: {name_lower}")
            provider_cls = provider_registry.get(name_lower)
            self._instances[name_lower] = provider_cls()
        return self._instances[name_lower]

    def get_configured_providers(self) -> list[str]:
        """
        List all providers that have keys/URLs configured in Settings.
        """
        return [
            name for name in provider_registry.list_registered()
            if self.is_configured(name)
        ]

    def get_failover_order(self, preferred: str | None = None) -> list[str]:
        """
        Return the list of configured providers ordered by priority.
        If preferred is provided, it is placed first.
        """
        configured = self.get_configured_providers()
        if not configured:
            return []

        # Sort based on priority list
        order = []
        if preferred and preferred.lower() in configured:
            order.append(preferred.lower())

        for name in self.priority_order:
            if name in configured and name not in order:
                order.append(name)

        # Append any configured providers not explicitly in the priority order list
        for name in configured:
            if name not in order:
                order.append(name)

        return order

    async def close_all(self) -> None:
        """
        Gracefully close all cached provider clients.
        """
        logger.info("Closing all cached provider instances.")
        for name, provider in self._instances.items():
            try:
                await provider.close()
            except Exception as exc:
                logger.error(f"Failed to close provider {name}: {exc}", exc_info=True)
        self._instances.clear()


# Singleton instance
provider_manager = ProviderManager()
