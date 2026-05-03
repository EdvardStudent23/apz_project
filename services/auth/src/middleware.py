from __future__ import annotations

from collections.abc import Awaitable, Callable

import structlog
from common.schemas import ApiResponse

from src.services.exceptions import DomainError

Scope = dict
Message = dict
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

logger = structlog.get_logger(__name__)


class ExceptionMiddleware:
    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except DomainError as exc:
            if response_started:
                raise
            await _send_error(send, exc.status_code, exc.message)
        except Exception as exc:
            logger.exception("unhandled exception", error=str(exc))
            if response_started:
                raise
            await _send_error(send, 500, "internal server error")


async def _send_error(send: Send, status: int, message: str) -> None:
    body = ApiResponse(status=False, response=message).model_dump_json().encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})
