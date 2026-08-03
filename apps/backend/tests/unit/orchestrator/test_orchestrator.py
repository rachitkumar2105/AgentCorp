"""Unit tests for ProviderService orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.provider_service import ProviderService
from app.providers.schemas import ChatRequest, ChatResponse, ChatMessage
from app.providers.exceptions import ProviderError


@pytest.mark.anyio
async def test_provider_service_manual_success():
    mock_provider = MagicMock()
    mock_chat = AsyncMock(return_value=ChatResponse(
        provider="mock",
        model="mock-model",
        content="Success Response",
        usage=None
    ))
    mock_provider.chat = mock_chat

    # Patch the provider manager to return our mock provider
    with patch("app.services.provider_service.provider_manager") as mock_mgr:
        mock_mgr.get_provider.return_value = mock_provider
        
        service = ProviderService(default_provider="mock")
        req = ChatRequest(messages=[ChatMessage(role="user", content="Hi")])
        res = await service.chat(req, provider_name="mock", mode="MANUAL")
        
        assert res.content == "Success Response"
        mock_chat.assert_called_once_with(req)


@pytest.mark.anyio
async def test_provider_service_auto_failover():
    mock_provider1 = MagicMock()
    mock_provider1.chat = AsyncMock(side_effect=ProviderError("Fail"))
    mock_provider1.supports_tools = True
    
    mock_provider2 = MagicMock()
    mock_provider2.chat = AsyncMock(return_value=ChatResponse(
        provider="mock2",
        model="mock-model2",
        content="Backup Success",
        usage=None
    ))
    mock_provider2.supports_tools = True

    with patch("app.services.provider_service.provider_manager") as mock_mgr:
        mock_mgr.get_failover_order.return_value = ["mock1", "mock2"]
        def get_prov(name):
            if name == "mock1":
                return mock_provider1
            return mock_provider2
        mock_mgr.get_provider.side_effect = get_prov

        service = ProviderService(default_provider="mock1")
        req = ChatRequest(messages=[ChatMessage(role="user", content="Hi")])
        res = await service.chat(req, mode="AUTO")
        
        assert res.content == "Backup Success"
        assert res.provider == "mock2"
        mock_provider1.chat.assert_called_once_with(req)
        mock_provider2.chat.assert_called_once_with(req)
