from __future__ import annotations


class DomainError(Exception):
    status_code: int = 400
    message: str = "domain error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class AccountNotFound(DomainError):
    status_code = 404
    message = "account not found"


class InsufficientFunds(DomainError):
    message = "insufficient funds"


class CurrencyMismatch(DomainError):
    message = "currency mismatch"


class InvalidAmount(DomainError):
    message = "invalid amount"
