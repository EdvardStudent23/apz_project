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


class UnauthorizedAccount(DomainError):
    status_code = 403
    message = "account does not belong to this user"


class HoldNotFound(DomainError):
    status_code = 404
    message = "hold not found"


class HoldAlreadyResolved(DomainError):
    status_code = 409
    message = "hold has already been released or completed"


class AccountClosed(DomainError):
    status_code = 409
    message = "account is closed"


class AccountNotEmpty(DomainError):
    status_code = 409
    message = "account cannot be closed while it still holds funds or has active holds"
