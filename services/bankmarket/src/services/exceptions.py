from __future__ import annotations


class DomainError(Exception):
    status_code: int = 400
    message: str = "domain error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)
