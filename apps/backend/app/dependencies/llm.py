"""
Dependency injection for Provider Service.
"""

from app.services.provider_service import ProviderService


def get_provider_service() -> ProviderService:
    """
    Dependency provider for ProviderService instance.
    """
    return ProviderService()
