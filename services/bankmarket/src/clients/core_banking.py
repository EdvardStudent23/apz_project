from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
import structlog

from src.services.exceptions import BankingCallFailed

logger = structlog.get_logger(__name__)


class CoreBankingClient:
    """Thin HTTP client for the core-banking service.

    Every call carries the buyer's bearer token so authorization is
    enforced server-side — the marketplace never holds money on an
    account it isn't authorized to touch.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)

    async def place_hold(
        self,
        *,
        bearer_token: str,
        account_id: UUID,
        amount: float,
        currency: str | None,
        reason: str,
        external_ref: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "account_id": str(account_id),
            "amount": float(amount),
            "reason": reason,
        }
        if currency is not None:
            payload["currency"] = currency
        if external_ref is not None:
            payload["external_ref"] = external_ref

        return await self._post("/holds", bearer_token, payload)

    async def release_hold(self, *, bearer_token: str, hold_id: UUID) -> dict[str, Any]:
        return await self._post(f"/holds/{hold_id}/release", bearer_token, body=None)

    async def _post(
        self,
        path: str,
        bearer_token: str,
        body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {bearer_token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=body, headers=headers)
        except httpx.HTTPError as exc:
            logger.error("core_banking_unreachable", url=url, error=str(exc))
            raise BankingCallFailed(f"core banking unreachable: {exc}") from exc

        if response.status_code >= 400:
            body_text = response.text
            logger.warning(
                "core_banking_error",
                url=url,
                status=response.status_code,
                body=body_text[:300],
            )
            raise BankingCallFailed(
                f"core banking returned {response.status_code}: {body_text[:200]}"
            )

        data = response.json()
        if isinstance(data, dict) and data.get("status") is False:
            raise BankingCallFailed(str(data.get("response") or "core banking error"))
        return data
