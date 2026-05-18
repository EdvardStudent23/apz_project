"""
E2E test fixtures and shared helpers.

These tests run against the full Docker Compose stack (`make up`).
Set E2E_BASE_URL to override the default Nginx gateway address.

Environment variables:
    E2E_BASE_URL        default http://localhost:8080  (Nginx gateway)
    AUTH_DIRECT_URL_1   default http://localhost:8001  (auth_1 direct)
    AUTH_DIRECT_URL_2   default http://localhost:8002  (auth_2 direct)
    CORE_BANKING_URL    default http://localhost:8003  (core_banking direct)
    HISTORY_URL         default http://localhost:8004  (history direct)
    BANKMARKET_URL      default http://localhost:8005  (bankmarket direct)
    RABBITMQ_API_URL    default http://localhost:15672 (RabbitMQ management)
"""
from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio

# ── Service URLs ──────────────────────────────────────────────────────────────
GATEWAY = os.getenv("E2E_BASE_URL", "http://localhost:8080")
AUTH_1 = os.getenv("AUTH_DIRECT_URL_1", "http://localhost:8001")
AUTH_2 = os.getenv("AUTH_DIRECT_URL_2", "http://localhost:8002")
CORE_BANKING = os.getenv("CORE_BANKING_URL", "http://localhost:8003")
HISTORY = os.getenv("HISTORY_URL", "http://localhost:8004")
BANKMARKET = os.getenv("BANKMARKET_URL", "http://localhost:8005")
RABBITMQ_API = os.getenv("RABBITMQ_API_URL", "http://localhost:15672")

# Unique prefix for test resources created in this run — avoids collision on re-runs
RUN_ID = uuid.uuid4().hex[:8]


# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class UserCredentials:
    username: str
    email: str
    password: str
    access_token: str = ""
    refresh_token: str = ""
    user_id: int = 0


@dataclass
class BankAccount:
    id: str
    currency: str
    balance: float


# ── Session-scoped event loop ─────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── HTTP client fixtures ──────────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def gateway() -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client pointed at the Nginx gateway (port 8080)."""
    async with httpx.AsyncClient(base_url=GATEWAY, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def auth1_direct() -> AsyncIterator[httpx.AsyncClient]:
    """Direct client to auth_1 replica (bypasses Nginx — used for failover tests)."""
    async with httpx.AsyncClient(base_url=AUTH_1, timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def auth2_direct() -> AsyncIterator[httpx.AsyncClient]:
    """Direct client to auth_2 replica."""
    async with httpx.AsyncClient(base_url=AUTH_2, timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def core_banking_direct() -> AsyncIterator[httpx.AsyncClient]:
    """Direct client to core_banking service."""
    async with httpx.AsyncClient(base_url=CORE_BANKING, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def history_direct() -> AsyncIterator[httpx.AsyncClient]:
    """Direct client to history service."""
    async with httpx.AsyncClient(base_url=HISTORY, timeout=30.0) as client:
        yield client


# ── Helper functions ──────────────────────────────────────────────────────────
async def register_user(client: httpx.AsyncClient, username: str, email: str, password: str) -> dict:
    r = await client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    assert r.status_code == 201, f"Register failed ({r.status_code}): {r.text}"
    return r.json()


async def login_user(client: httpx.AsyncClient, username: str, password: str) -> dict:
    r = await client.post("/auth/login", json={
        "username": username,
        "password": password,
    })
    assert r.status_code == 200, f"Login failed ({r.status_code}): {r.text}"
    return r.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def poll_until(
    coro_factory,
    *,
    check,
    timeout_s: float = 15.0,
    interval_s: float = 1.0,
) -> object:
    """Retry ``coro_factory()`` every ``interval_s`` seconds until ``check(result)``
    is truthy or ``timeout_s`` elapses. Returns the passing result."""
    deadline = asyncio.get_event_loop().time() + timeout_s
    last_result = None
    while asyncio.get_event_loop().time() < deadline:
        last_result = await coro_factory()
        if check(last_result):
            return last_result
        await asyncio.sleep(interval_s)
    raise TimeoutError(
        f"Condition not met within {timeout_s}s. Last result: {last_result}"
    )


# ── Session-wide fixtures: registered user + accounts ────────────────────────
@pytest_asyncio.fixture(scope="session")
async def alice(gateway: httpx.AsyncClient) -> UserCredentials:
    """Registers alice once for the whole test session."""
    creds = UserCredentials(
        username=f"alice_{RUN_ID}",
        email=f"alice_{RUN_ID}@nanobank.test",
        password="AliceSecret1",
    )
    data = await register_user(gateway, creds.username, creds.email, creds.password)
    creds.user_id = data["user"]["id"]

    login_data = await login_user(gateway, creds.username, creds.password)
    creds.access_token = login_data["tokens"]["access_token"]
    creds.refresh_token = login_data["tokens"]["refresh_token"]
    return creds


@pytest_asyncio.fixture(scope="session")
async def bob(gateway: httpx.AsyncClient) -> UserCredentials:
    """Registers bob once for the whole test session."""
    creds = UserCredentials(
        username=f"bob_{RUN_ID}",
        email=f"bob_{RUN_ID}@nanobank.test",
        password="BobSecret42",
    )
    data = await register_user(gateway, creds.username, creds.email, creds.password)
    creds.user_id = data["user"]["id"]

    login_data = await login_user(gateway, creds.username, creds.password)
    creds.access_token = login_data["tokens"]["access_token"]
    creds.refresh_token = login_data["tokens"]["refresh_token"]
    return creds


@pytest_asyncio.fixture(scope="session")
async def alice_accounts(
    gateway: httpx.AsyncClient,
    alice: UserCredentials,
) -> list[BankAccount]:
    """Creates one USD account for alice."""
    r = await gateway.post(
        "/accounts",
        json={"currency": "USD"},
        headers=auth_headers(alice.access_token),
    )
    assert r.status_code == 200, f"Create account failed: {r.text}"
    data = r.json()["response"]
    return [BankAccount(id=data["id"], currency=data["currency"], balance=data["balance"])]


@pytest_asyncio.fixture(scope="session")
async def bob_accounts(
    gateway: httpx.AsyncClient,
    bob: UserCredentials,
) -> list[BankAccount]:
    """Creates one USD account for bob."""
    r = await gateway.post(
        "/accounts",
        json={"currency": "USD"},
        headers=auth_headers(bob.access_token),
    )
    assert r.status_code == 200, f"Create account failed: {r.text}"
    data = r.json()["response"]
    return [BankAccount(id=data["id"], currency=data["currency"], balance=data["balance"])]
