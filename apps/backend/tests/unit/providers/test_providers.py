"""Unit tests for Provider Registry."""
import pytest
from app.providers.registry import provider_registry, ProviderRegistry
from app.providers.exceptions import ProviderNotFoundError


def test_provider_registry_operations():
    registry = ProviderRegistry()
    
    # Check registration
    class FakeProvider:
        pass
        
    registry.register("fake", FakeProvider)
    assert registry.exists("fake")
    assert registry.get("fake") == FakeProvider
    
    # Check unregister
    registry.unregister("fake")
    assert not registry.exists("fake")
    
    with pytest.raises(ProviderNotFoundError):
        registry.get("fake")
