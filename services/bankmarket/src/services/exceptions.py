from __future__ import annotations


class DomainError(Exception):
    status_code: int = 400
    message: str = "domain error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class ProductNotFound(DomainError):
    status_code = 404
    message = "product not found"


class ProductNotApproved(DomainError):
    status_code = 409
    message = "product is not approved for sale"


class InvalidProductState(DomainError):
    status_code = 409
    message = "product cannot be moderated in its current state"


class NotOwnerOrAdmin(DomainError):
    status_code = 403
    message = "only the owner or an admin can perform this action"


class OrderNotFound(DomainError):
    status_code = 404
    message = "order not found"


class BankingCallFailed(DomainError):
    status_code = 502
    message = "core banking call failed"
