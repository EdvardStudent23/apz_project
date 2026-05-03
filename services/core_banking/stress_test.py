from __future__ import annotations

import asyncio
import time
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configuration
CORE_BANKING_URL = "http://localhost:8003"
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/core_banking"


async def setup_funds(account_id: str, amount: float):
    """Direct DB access to seed funds for testing."""
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE accounts SET balance = :balance WHERE id = :id"),
            {"balance": amount, "id": account_id},
        )
    await engine.dispose()


async def run_stress_test():
    print("Starting Resilience and Stress Test...")

    # Bypass auth
    headers = {"Authorization": "Bearer debug-token"}
    
    async with httpx.AsyncClient() as client:
        # 1. Setup
        print("\n1. Setting up accounts for stress test...")
        res_a = await client.post(f"{CORE_BANKING_URL}/accounts", json={"currency": "USD"}, headers=headers)
        res_a.raise_for_status()
        res_b = await client.post(f"{CORE_BANKING_URL}/accounts", json={"currency": "USD"}, headers=headers)
        res_b.raise_for_status()
        
        acc_a = res_a.json()["response"]["id"]
        acc_b = res_b.json()["response"]["id"]
        
        await setup_funds(acc_a, 1000.0)
        await setup_funds(acc_b, 1000.0)
        print(f"Account A: {acc_a}, Account B: {acc_b} (Seeded with 1000.0 USD each)")

        # 2. Deadlock/Concurrency Test
        print("\n2. Concurrency Test: 50 parallel bidirectional transfers (A<->B)...")
        
        async def do_transfer(sender, receiver, amount):
            try:
                resp = await client.post(
                    f"{CORE_BANKING_URL}/transfers",
                    json={"sender_account_id": sender, "receiver_account_id": receiver, "amount": amount},
                    headers=headers
                )
                resp.raise_for_status()
            except Exception as e:
                print(f"Transfer error: {e}")
                if hasattr(e, 'response'):
                    print(f"Error details: {e.response.text}")

        tasks = []
        for _ in range(25):
            tasks.append(do_transfer(acc_a, acc_b, 10.0))
            tasks.append(do_transfer(acc_b, acc_a, 10.0))

        start_time = time.perf_counter()
        await asyncio.gather(*tasks)
        end_time = time.perf_counter()
        
        print(f"Concurrency test finished in {end_time - start_time:.2f}s")

        # Verify Balances
        res_bal = await client.get(f"{CORE_BANKING_URL}/accounts", headers=headers)
        res_bal.raise_for_status()
        print("\nFinal Balances (should both be 1000.0):")
        for acc in res_bal.json()["response"]:
            if acc["id"] in [acc_a, acc_b]:
                print(f"Account {acc['id']}: {acc['balance']} {acc['currency']}")

        # 3. Currency Conversion Test (USD -> UAH)
        print("\n3. Currency Conversion Test (USD -> UAH)...")
        res_uah = await client.post(f"{CORE_BANKING_URL}/accounts", json={"currency": "UAH"}, headers=headers)
        res_uah.raise_for_status()
        acc_uah = res_uah.json()["response"]["id"]
        
        print(f"Transferring 100 USD from {acc_a} to {acc_uah} (UAH)...")
        res_tx = await client.post(
            f"{CORE_BANKING_URL}/transfers",
            json={"sender_account_id": acc_a, "receiver_account_id": acc_uah, "amount": 100.0},
            headers=headers
        )
        if res_tx.status_code != 200:
            print(f"Transfer failed: {res_tx.text}")
        res_tx.raise_for_status()
        
        res_bal = await client.get(f"{CORE_BANKING_URL}/accounts", headers=headers)
        res_bal.raise_for_status()
        for acc in res_bal.json()["response"]:
            if acc["id"] == acc_uah:
                print(f"UAH Account {acc['id']} balance: {acc['balance']} (Expected ~3950.0)")
            if acc["id"] == acc_a:
                print(f"USD Account {acc['id']} balance: {acc['balance']} (Expected ~900.0)")

        # 4. Resilience Test (Transactional Outbox)
        print("\n4. Outbox Resilience Test...")
        # Check unprocessed events count
        engine = create_async_engine(DB_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT count(*) FROM outbox_events WHERE processed = False"))
            count = result.scalar()
            print(f"Unprocessed events in outbox: {count}")
            
        print("Done. Resilience is confirmed if outbox count remains low (meaning relay is working).")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
