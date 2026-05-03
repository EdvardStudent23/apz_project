from __future__ import annotations

from uuid import uuid4
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.api import app
from src.routes.common.deps import get_current_user


@pytest.fixture
async def api_client(db_engine):
    # Setup app state for tests
    app.state.db_sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    app.state.jwks = {"keys": []}
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_api_create_account(api_client):
    user_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: user_id
    
    response = await api_client.post(
        "/accounts",
        json={"currency": "USD"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] is True
    assert response.json()["response"]["currency"] == "USD"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_list_accounts(api_client):
    user_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: user_id
    
    # Create one first
    await api_client.post("/accounts", json={"currency": "USD"})
    
    response = await api_client.get("/accounts")
    assert response.status_code == 200
    assert len(response.json()["response"]) == 1
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_transfer(api_client):
    user_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: user_id
    
    # Create accounts
    res1 = await api_client.post("/accounts", json={"currency": "USD"})
    acc1_id = res1.json()["response"]["id"]
    res2 = await api_client.post("/accounts", json={"currency": "USD"})
    acc2_id = res2.json()["response"]["id"]
    
    # Manually add funds (via DB session fixture if we had it here, but we can do it via repository)
    response = await api_client.post(
        "/transfers",
        json={
            "sender_account_id": str(acc1_id),
            "receiver_account_id": str(acc2_id),
            "amount": 100.0,
            "purpose": "API test"
        }
    )
    
    # Should fail with 400 because balance is 0
    assert response.status_code == 400
    assert "available 0.0" in response.json()["response"].lower()
    
    # Test currency mismatch
    res3 = await api_client.post("/accounts", json={"currency": "EUR"})
    acc3_id = res3.json()["response"]["id"]
    response = await api_client.post(
        "/transfers",
        json={
            "sender_account_id": str(acc1_id),
            "receiver_account_id": str(acc3_id),
            "amount": 10.0
        }
    )
    assert response.status_code == 400
    assert "between usd and eur" in response.json()["response"].lower()

    # Test account not found
    response = await api_client.post(
        "/transfers",
        json={
            "sender_account_id": str(acc1_id),
            "receiver_account_id": str(uuid4()),
            "amount": 10.0
        }
    )
    assert response.status_code == 404
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_unhandled_error(api_client):
    app.dependency_overrides[get_current_user] = lambda: uuid4()
    
    # Force an unhandled error in a route
    with patch("src.routes.banking.BankingService.get_user_accounts", side_effect=Exception("BOOM")):
        response = await api_client.get("/accounts")
        assert response.status_code == 500
        assert "internal server error" in response.json()["response"].lower()
    
    app.dependency_overrides.clear()
