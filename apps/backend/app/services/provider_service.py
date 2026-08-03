"""
Provider Service to manage execution and automatic failover of AI providers.
"""

import logging
import time
from collections.abc import AsyncGenerator

from app.config.settings import settings
from app.providers import provider_manager
from app.providers.exceptions import ProviderConfigurationError, ProviderError
from app.providers.schemas import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, StreamChunk

logger = logging.getLogger(__name__)


class ProviderService:
    """
    Business service for managing AI providers.
    Services outside the provider layer MUST only use this service.
    """

    def __init__(self, default_provider: str | None = None) -> None:
        self.default_provider = default_provider or settings.DEFAULT_PROVIDER

    async def chat(
        self,
        request: ChatRequest,
        provider_name: str | None = None,
        mode: str = "AUTO",
    ) -> ChatResponse:
        """
        Execute chat completion through the resolved provider with failover support.
        Modes:
          - AUTO: Try the preferred provider, then automatically failover to other configured providers.
          - MANUAL: Execute request strictly on the specified provider.
          - AGENT_DEFAULT: Fallback to the agent's default provider (supplied as provider_name).
        """
        resolved_preferred = provider_name or self.default_provider

        if mode == "MANUAL":
            logger.info(f"ProviderService: Executing chat request in MANUAL mode on {resolved_preferred}")
            provider = provider_manager.get_provider(resolved_preferred)
            return await provider.chat(request)

        # For AUTO and AGENT_DEFAULT, get failover order
        failover_list = provider_manager.get_failover_order(resolved_preferred)
        if not failover_list:
            raise ProviderConfigurationError("No AI Providers are configured and available in the system.")

        errors = []
        for current_provider_name in failover_list:
            logger.info(f"ProviderService: Attempting chat with provider: {current_provider_name}")
            start_time = time.perf_counter()
            try:
                provider = provider_manager.get_provider(current_provider_name)
                
                # Check capability if request specifies tools
                if getattr(request, "tools", None) and not provider.supports_tools:
                    logger.warning(f"Provider {current_provider_name} does not support tools. Skipping.")
                    continue

                response = await provider.chat(request)
                latency = time.perf_counter() - start_time
                logger.info(
                    f"ProviderService: Successful execution on {current_provider_name} "
                    f"using model {request.model} in {latency:.4f}s"
                )
                return response
            except Exception as exc:
                latency = time.perf_counter() - start_time
                logger.warning(
                    f"ProviderService: Execution failed on {current_provider_name} "
                    f"after {latency:.4f}s: {exc}. Trying next provider."
                )
                errors.append(f"{current_provider_name}: {exc}")

        # If we reach here, all providers in the failover list failed
        raise ProviderError(
            f"All configured providers failed to execute chat request. Errors: {'; '.join(errors)}"
        )

    async def embeddings(
        self,
        request: EmbeddingRequest,
        provider_name: str | None = None,
        mode: str = "AUTO",
    ) -> EmbeddingResponse:
        """
        Generate text embeddings with failover support.
        """
        resolved_preferred = provider_name or self.default_provider

        if mode == "MANUAL":
            logger.info(f"ProviderService: Executing embeddings request in MANUAL mode on {resolved_preferred}")
            provider = provider_manager.get_provider(resolved_preferred)
            return await provider.embeddings(request)

        failover_list = provider_manager.get_failover_order(resolved_preferred)
        if not failover_list:
            raise ProviderConfigurationError("No AI Providers are configured and available in the system.")

        errors = []
        for current_provider_name in failover_list:
            logger.info(f"ProviderService: Attempting embeddings with provider: {current_provider_name}")
            start_time = time.perf_counter()
            try:
                provider = provider_manager.get_provider(current_provider_name)
                
                if not provider.supports_embeddings:
                    logger.warning(f"Provider {current_provider_name} does not support embeddings. Skipping.")
                    continue

                response = await provider.embeddings(request)
                latency = time.perf_counter() - start_time
                logger.info(
                    f"ProviderService: Successful embeddings execution on {current_provider_name} "
                    f"in {latency:.4f}s"
                )
                return response
            except Exception as exc:
                latency = time.perf_counter() - start_time
                logger.warning(
                    f"ProviderService: Embeddings failed on {current_provider_name} "
                    f"after {latency:.4f}s: {exc}. Trying next provider."
                )
                errors.append(f"{current_provider_name}: {exc}")

        raise ProviderError(
            f"All configured providers failed to execute embeddings request. Errors: {'; '.join(errors)}"
        )

    async def health_check(self, provider_name: str | None = None) -> bool:
        """
        Run health check on the resolved provider.
        """
        resolved = provider_name or self.default_provider
        try:
            provider = provider_manager.get_provider(resolved)
            return await provider.health_check()
        except Exception as exc:
            logger.warning(f"Health check failed for provider {resolved}: {exc}")
            return False

    async def list_models(self, provider_name: str | None = None) -> list[str]:
        """
        List models of the resolved provider.
        """
        resolved = provider_name or self.default_provider
        provider = provider_manager.get_provider(resolved)
        return await provider.list_models()

    async def stream_chat(
        self,
        request: ChatRequest,
        provider_name: str | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat completion tokens from the resolved provider.

        Unlike ``chat()``, streaming does NOT perform automatic failover once
        the stream has started — switching providers mid-stream would corrupt
        the token sequence.  The provider is resolved once up-front; if it is
        unavailable the method raises immediately so the caller can inform the
        client before the SSE response starts.

        Args:
            request      : The normalised chat request (model, messages, params).
            provider_name: Optional override.  Defaults to ``self.default_provider``.

        Yields:
            StreamChunk objects in the order emitted by the provider.

        Raises:
            ProviderConfigurationError : No providers are configured.
            ProviderNotFoundError      : Requested provider is not registered.
            ProviderStreamingError     : Provider stream failed.
        """
        resolved = provider_name or self.default_provider
        logger.info(
            f"ProviderService: Starting stream_chat on provider={resolved} model={request.model}"
        )

        if not provider_manager.get_configured_providers():
            raise ProviderConfigurationError(
                "No AI Providers are configured and available in the system."
            )

        provider = provider_manager.get_provider(resolved)

        if not provider.supports_streaming:
            raise ProviderConfigurationError(
                f"Provider '{resolved}' does not support streaming."
            )

        # Delegate directly — the provider owns the async generator lifecycle
        async for chunk in await provider.stream_chat(request):
            yield chunk
