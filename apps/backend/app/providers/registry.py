"""
Provider Registry for locating and registering AI provider classes.
"""

from typing import Dict, Type

from app.providers.base import BaseProvider
from app.providers.exceptions import ProviderNotFoundError


class ProviderRegistry:
    """
    Registry for pluggable AI provider backends.
    Stores classes, not instances.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, Type[BaseProvider]] = {}

    def register(self, name: str, provider_cls: Type[BaseProvider]) -> None:
        """Register a new provider class."""
        self._providers[name.lower()] = provider_cls

    def get(self, name: str) -> Type[BaseProvider]:
        """Retrieve a provider class by its registered name."""
        provider_cls = self._providers.get(name.lower())
        if not provider_cls:
            raise ProviderNotFoundError(f"AI Provider '{name}' is not registered or supported.")
        return provider_cls

    def exists(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name.lower() in self._providers

    def unregister(self, name: str) -> None:
        """Remove a provider from the registry."""
        if name.lower() in self._providers:
            del self._providers[name.lower()]

    def list_registered(self) -> list[str]:
        """List all currently registered provider names."""
        return list(self._providers.keys())


# Singleton instance
provider_registry = ProviderRegistry()

# Register the default implementations at the end of the module to prevent circular imports
from app.providers.anthropic import AnthropicProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider
from app.providers.openrouter import OpenRouterProvider

provider_registry.register("groq", GroqProvider)
provider_registry.register("openai", OpenAIProvider)
provider_registry.register("gemini", GeminiProvider)
provider_registry.register("anthropic", AnthropicProvider)
provider_registry.register("openrouter", OpenRouterProvider)
provider_registry.register("ollama", OllamaProvider)
