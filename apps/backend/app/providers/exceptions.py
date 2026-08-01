"""
Custom exceptions for the provider layer.

These exceptions provide a consistent error model across all AI providers.
The rest of the application should only interact with these exceptions,
never provider-specific SDK exceptions.
"""


class ProviderError(Exception):
    """Base exception for all provider-related errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is incorrectly configured."""

    pass


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails."""

    pass


class ProviderConnectionError(ProviderError):
    """Raised when the provider cannot be reached."""

    pass


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""

    pass


class ProviderRateLimitError(ProviderError):
    """Raised when the provider rate limit has been exceeded."""

    pass


class ProviderQuotaExceededError(ProviderError):
    """Raised when the provider account quota has been exhausted."""

    pass


class ProviderBadRequestError(ProviderError):
    """Raised when an invalid request is sent to the provider."""

    pass


class ProviderNotFoundError(ProviderError):
    """Raised when the requested model or resource does not exist."""

    pass


class ProviderResponseError(ProviderError):
    """Raised when the provider returns an invalid or unexpected response."""

    pass


class ProviderModelNotSupportedError(ProviderError):
    """Raised when the requested model is not supported by the provider."""

    pass


class ProviderToolExecutionError(ProviderError):
    """Raised when tool execution fails."""

    pass


class ProviderStreamingError(ProviderError):
    """Raised when a streaming request fails."""

    pass