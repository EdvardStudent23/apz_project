from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from src.api import lifespan


@pytest.mark.asyncio
async def test_lifespan_direct():
    app = FastAPI()
    
    with patch("src.api.httpx.AsyncClient") as mock_client_class, \
         patch("src.api.OutboxRelay") as mock_relay, \
         patch("src.api.make_engine") as mock_engine, \
         patch("src.api.make_session_factory"):
        
        # Setup mock for httpx client
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"keys": [{"kid": "test"}]}
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_relay_instance = mock_relay.return_value
        mock_relay_instance.start = AsyncMock()
        mock_relay_instance.stop = AsyncMock()
        
        mock_engine.return_value.dispose = AsyncMock()

        # Call the lifespan generator
        async with lifespan(app):
            assert app.state.jwks["keys"][0]["kid"] == "test"
            assert mock_relay_instance.start.called
        
        assert mock_relay_instance.stop.called
        assert mock_engine.return_value.dispose.called
