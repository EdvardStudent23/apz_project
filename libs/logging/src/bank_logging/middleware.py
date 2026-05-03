from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog

Scope = dict
Message = dict
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]


class RequestIdMiddleware:
    HEADER = b"x-request-id"

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._extract(scope) or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.HEADER, request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")

    @staticmethod
    def _extract(scope: Scope) -> str | None:
        for name, value in scope.get("headers", []):
            if name == RequestIdMiddleware.HEADER:
                return value.decode()
        return None
