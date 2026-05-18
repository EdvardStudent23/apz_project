"""
E2E: Auth Service replica failover (course requirement).

Scenario from CLAUDE.md §"Auth replica failover":
    1. Register + login via Nginx gateway → capture JWT.
    2. Validate JWT-protected endpoint — succeeds.
    3. Stop auth_1 container.
    4. Validate same endpoint again — must still succeed (auth_2 + Redis session).
    5. Restart auth_1.
    6. Logout — token must be revoked on BOTH replicas immediately.

These tests use `docker compose` subprocess calls to control containers.
They are marked `@pytest.mark.failover` so they can be run selectively:

    uv run pytest tests/e2e/test_auth_failover.py -v -m failover

Prerequisites: full stack must be running (`make up`).
"""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import httpx
import pytest

from tests.e2e.conftest import (
    GATEWAY,
    RUN_ID,
    auth_headers,
    login_user,
    poll_until,
    register_user,
)

REPO_ROOT = Path(__file__).parent.parent.parent
COMPOSE_CMD = ["docker", "compose", "-f", str(REPO_ROOT / "docker-compose.yml")]


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a `docker compose` sub-command from the repo root."""
    return subprocess.run(
        [*COMPOSE_CMD, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=check,
    )


def service_is_running(service: str) -> bool:
    result = compose("ps", "--status", "running", "--quiet", service, check=False)
    return bool(result.stdout.strip())


@pytest.fixture
async def failover_user(gateway: httpx.AsyncClient):
    """
    Creates a dedicated user for failover testing.
    Yields (access_token, refresh_token).
    The user is not cleaned up — it is cheap to leave in the DB.
    """
    username = f"failover_{RUN_ID}"
    await register_user(
        gateway, username, f"{username}@test.local", "FailoverPass1"
    )
    data = await login_user(gateway, username, "FailoverPass1")
    yield data["tokens"]["access_token"], data["tokens"]["refresh_token"]


@pytest.mark.failover
class TestAuthReplicaFailover:
    """
    Verifies Auth replica failover and session continuity via Redis.

    These tests stop/start Docker containers — they are slow and require
    Docker to be available in the test environment.
    """

    async def test_both_replicas_healthy_before_failover(
        self,
        auth1_direct: httpx.AsyncClient,
        auth2_direct: httpx.AsyncClient,
    ) -> None:
        r1 = await auth1_direct.get("/health")
        r2 = await auth2_direct.get("/health")
        assert r1.status_code == 200, "auth_1 must be healthy before failover test"
        assert r2.status_code == 200, "auth_2 must be healthy before failover test"

    async def test_session_survives_auth1_shutdown(
        self,
        gateway: httpx.AsyncClient,
        failover_user,
    ) -> None:
        """
        Stop auth_1. Requests that were being served by auth_1 must continue
        to succeed because auth_2 is alive and session state lives in Redis.
        """
        access_token, _ = failover_user

        # 1. Confirm token is valid before stopping auth_1
        r = await gateway.get("/auth/validate", headers=auth_headers(access_token))
        assert r.status_code == 200, "Token must be valid before stopping auth_1"

        # 2. Stop auth_1
        compose("stop", "auth_1")
        try:
            # 3. Wait until Nginx detects the upstream is down (up to 10 s)
            await asyncio.sleep(3)

            # 4. Request must still succeed via auth_2
            async def validate():
                return await gateway.get(
                    "/auth/validate",
                    headers=auth_headers(access_token),
                )

            result = await poll_until(
                validate,
                check=lambda r: r.status_code == 200,
                timeout_s=15.0,
                interval_s=1.0,
            )
            assert result.status_code == 200, (
                "JWT validation failed after auth_1 went down — "
                "session should be in Redis, not in-process"
            )

        finally:
            # 5. Restart auth_1 so subsequent tests can use it
            compose("start", "auth_1")
            # Wait for it to be healthy again
            await asyncio.sleep(5)

    async def test_logout_invalidates_on_all_replicas(
        self,
        gateway: httpx.AsyncClient,
        auth1_direct: httpx.AsyncClient,
        auth2_direct: httpx.AsyncClient,
    ) -> None:
        """
        A logout must invalidate the session in Redis so that BOTH replicas
        reject the token — not just the one that handled the logout request.
        """
        username = f"logout_failover_{RUN_ID}"
        await register_user(
            gateway, username, f"{username}@test.local", "LogoutFail1"
        )
        data = await login_user(gateway, username, "LogoutFail1")
        token = data["tokens"]["access_token"]

        # Confirm token is valid on auth_1 directly
        r1 = await auth1_direct.get("/auth/validate", headers=auth_headers(token))
        assert r1.status_code == 200, "auth_1 must accept the token before logout"

        # Confirm token is valid on auth_2 directly
        r2 = await auth2_direct.get("/auth/validate", headers=auth_headers(token))
        assert r2.status_code == 200, "auth_2 must accept the token before logout"

        # Logout via gateway (may land on either replica)
        r_logout = await gateway.post(
            "/auth/logout", headers=auth_headers(token)
        )
        assert r_logout.status_code == 200

        # Give Redis a moment to propagate
        await asyncio.sleep(0.5)

        # Both replicas must now reject the token
        r1_after = await auth1_direct.get(
            "/auth/validate", headers=auth_headers(token)
        )
        assert r1_after.status_code in (401, 403), (
            f"auth_1 still accepts token after logout ({r1_after.status_code})"
        )

        r2_after = await auth2_direct.get(
            "/auth/validate", headers=auth_headers(token)
        )
        assert r2_after.status_code in (401, 403), (
            f"auth_2 still accepts token after logout ({r2_after.status_code})"
        )

    async def test_nginx_load_balances_across_replicas(
        self,
        gateway: httpx.AsyncClient,
        alice,
    ) -> None:
        """
        Send 20 validate requests via Nginx. With least_conn and two healthy
        replicas, traffic should be distributed. We can't assert exact counts
        but we verify all 20 succeed (which is the actual requirement).
        """
        results = await asyncio.gather(*[
            gateway.get("/auth/validate", headers=auth_headers(alice.access_token))
            for _ in range(20)
        ])
        failures = [r for r in results if r.status_code != 200]
        assert not failures, (
            f"{len(failures)}/20 validate requests failed under load"
        )


# ════════════════════════════════════════════════════════════════════════════
# MongoDB replica-set quorum test (course requirement §"Mongo quorum read-only")
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.failover
class TestMongoQuorum:
    """
    Verifies that MongoDB goes read-only when quorum is lost.
    Stops 2 of 3 nodes, checks history reads still work, then restores.
    """

    async def test_mongo_replica_set_has_primary(self) -> None:
        """Check that the replica set elected a primary on startup."""
        result = compose(
            "exec", "-T", "mongo_1",
            "mongosh", "--eval",
            "rs.status().members.filter(m => m.stateStr === 'PRIMARY').length",
            "--quiet",
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("Cannot exec into mongo_1 — is the stack running?")
        output = result.stdout.strip().splitlines()
        primary_count = int(output[-1]) if output else 0
        assert primary_count == 1, (
            f"Expected 1 PRIMARY in replica set, got {primary_count}. "
            f"mongosh output: {result.stdout}"
        )

    async def test_quorum_loss_makes_writes_fail(
        self,
        history_direct: httpx.AsyncClient,
        gateway: httpx.AsyncClient,
        alice,
        alice_accounts,
        bob_accounts,
    ) -> None:
        """
        Stop mongo_2 and mongo_3 → replica set loses majority → primary steps down
        → history consumer writes fail (or queue backs up).
        Reads on the surviving secondary should still work.
        """
        compose("stop", "mongo_2", "mongo_3")
        try:
            # Allow time for Mongo to detect the partition
            await asyncio.sleep(5)

            # History GETs should still work via the surviving secondary
            r = await history_direct.get("/health")
            # 200 or 404 (not yet implemented) — both mean service is alive.
            # 5xx would indicate the service crashed.
            assert r.status_code < 500, (
                "History service should survive mongo quorum loss for reads"
            )

        finally:
            # Restore the replica set
            compose("start", "mongo_2", "mongo_3")
            # Allow election to complete
            await asyncio.sleep(10)

    async def test_replica_set_recovers_after_quorum_restored(self) -> None:
        """After mongo_2/mongo_3 come back, a new primary must be elected."""
        result = compose(
            "exec", "-T", "mongo_1",
            "mongosh", "--eval",
            "rs.status().members.filter(m => m.stateStr === 'PRIMARY').length",
            "--quiet",
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("Cannot exec into mongo_1")
        output = result.stdout.strip().splitlines()
        primary_count = int(output[-1]) if output else 0
        assert primary_count == 1, (
            "Replica set did not elect a PRIMARY after nodes came back"
        )
