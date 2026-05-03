from __future__ import annotations

import asyncio
import uuid
from typing import Any

import httpx

# Configuration
GATEWAY_URL = "http://localhost:8080"  # Through Nginx
CORE_BANKING_URL = "http://localhost:8003"  # Direct (for dev/testing)
AUTH_URL = "http://localhost:8001"


class NanoBankClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url
        self.headers = {"X-Request-Id": str(uuid.uuid4())}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def create_account(self, currency: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/accounts",
                json={"currency": currency},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["response"]

    async def list_accounts(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["response"]

    async def transfer(
        self, sender_id: str, receiver_id: str, amount: float, purpose: str | None = None
    ) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transfers",
                json={
                    "sender_account_id": sender_id,
                    "receiver_account_id": receiver_id,
                    "amount": amount,
                    "purpose": purpose,
                },
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["response"]


def convert_currency(amount: float, from_curr: str, to_curr: str) -> float:
    """
    Example client-side currency conversion.
    In a real app, this might call a dedicated 'ExchangeRateService'.
    """
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "UAH": 39.5,
    }
    # Convert to USD base first
    usd_amount = amount / rates[from_curr]
    # Convert to target
    return usd_amount * rates[to_curr]


async def run_demo():
    print("Starting NanoBank Core Banking Demo...")

    # Set this to True to bypass auth if the Auth service isn't running
    DEBUG_BYPASS_AUTH = True
    token = "debug-token"
    
    if DEBUG_BYPASS_AUTH:
        print("INFO: Authentication bypass enabled for local testing.")

    client = NanoBankClient(CORE_BANKING_URL, token=token)

    print("\n1. Creating Accounts...")
    try:
        acc1 = await client.create_account("USD")
        print(f"Created First USD Account: {acc1['id']}")

        acc2 = await client.create_account("USD")
        print(f"Created Second USD Account: {acc2['id']}")

        print("\n2. Checking Balances...")
        accounts = await client.list_accounts()
        for acc in accounts:
            print(f"Account {acc['id']}: {acc['balance']} {acc['currency']}")

        print("\n3. Simulating Client-Side Logic (Currency Conversion)...")
        amount_to_save_uah = 1000.0
        equivalent_usd = convert_currency(amount_to_save_uah, "UAH", "USD")
        print(f"Note: {amount_to_save_uah} UAH is approximately {equivalent_usd:.2f} USD")

        print("\n4. Attempting a Transfer...")
        print("Initiating 50 USD transfer between the two USD accounts (expecting failure due to 0 balance)...")
        try:
            await client.transfer(acc1["id"], acc2["id"], 50.0, "Monthly Savings")
        except httpx.HTTPStatusError as e:
            print(f"Expected Transfer Failure: {e.response.json()['response']}")

    except httpx.ConnectError:
        print("Error: Could not connect to the service. Is it running?")
        print("Tip: Start the service with 'uv run uvicorn src.api:app --port 8003'")


if __name__ == "__main__":
    asyncio.run(run_demo())
