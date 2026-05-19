from __future__ import annotations

from uuid import UUID

from src.clients.core_banking import CoreBankingClient
from src.db.repository import MarketRepository, Order, Product
from src.services.exceptions import (
    InvalidProductState,
    NotOwnerOrAdmin,
    OrderNotFound,
    ProductNotApproved,
    ProductNotFound,
)


class MarketService:
    def __init__(self, repository: MarketRepository, banking: CoreBankingClient) -> None:
        self.repository = repository
        self.banking = banking

    # ── Products ────────────────────────────────────────────────────────

    async def create_product(
        self,
        owner_id: UUID,
        name: str,
        description: str,
        price: float,
        currency: str,
    ) -> Product:
        return await self.repository.create_product(
            owner_id=owner_id,
            name=name.strip(),
            description=description.strip(),
            price=price,
            currency=currency.upper(),
        )

    async def list_approved(self) -> list[Product]:
        return await self.repository.list_products_by_status("approved")

    async def list_pending(self) -> list[Product]:
        return await self.repository.list_products_by_status("pending")

    async def list_mine(self, owner_id: UUID) -> list[Product]:
        return await self.repository.list_products_for_owner(owner_id)

    async def moderate(
        self,
        product_id: UUID,
        decision: str,
        moderation_note: str | None = None,
    ) -> Product:
        if decision not in {"approved", "rejected"}:
            raise InvalidProductState(f"unknown moderation decision: {decision}")
        product = await self.repository.get_product(product_id)
        if not product:
            raise ProductNotFound()
        if product.status != "pending":
            raise InvalidProductState(
                f"product is already {product.status}, cannot moderate again"
            )
        updated = await self.repository.set_product_status(
            product_id, decision, moderation_note
        )
        if not updated:
            raise ProductNotFound()
        return updated

    async def delete_listing(self, product_id: UUID, requester_id: UUID, is_admin: bool) -> None:
        product = await self.repository.get_product(product_id)
        if not product:
            raise ProductNotFound()
        if product.owner_id != requester_id and not is_admin:
            raise NotOwnerOrAdmin()
        # Soft-delete via status = 'rejected' to keep the audit trail in Neo4j.
        await self.repository.set_product_status(product_id, "rejected", "withdrawn")

    # ── Orders ──────────────────────────────────────────────────────────

    async def place_order(
        self,
        *,
        product_id: UUID,
        buyer_id: UUID,
        buyer_account_id: UUID,
        bearer_token: str,
    ) -> Order:
        product = await self.repository.get_product(product_id)
        if not product:
            raise ProductNotFound()
        if product.status != "approved":
            raise ProductNotApproved()

        # Place a hold against the buyer's account. Core banking does the
        # currency conversion if the buyer's account is in a different
        # currency than the product.
        banking_response = await self.banking.place_hold(
            bearer_token=bearer_token,
            account_id=buyer_account_id,
            amount=product.price,
            currency=product.currency,
            reason=f"market:{product.id}",
            external_ref=str(product.id),
        )

        hold_payload = banking_response.get("response") or {}
        hold_id = UUID(hold_payload["id"])
        held_amount = float(hold_payload.get("amount", product.price))
        held_currency = str(hold_payload.get("currency", product.currency))

        return await self.repository.create_order(
            product_id=product.id,
            buyer_id=buyer_id,
            hold_id=hold_id,
            amount=held_amount,
            currency=held_currency,
        )

    async def cancel_order(
        self,
        *,
        order_id: UUID,
        buyer_id: UUID,
        bearer_token: str,
    ) -> Order:
        order = await self.repository.get_order(order_id)
        if not order:
            raise OrderNotFound()
        if order.buyer_id != buyer_id:
            raise NotOwnerOrAdmin()
        if order.status != "placed":
            return order

        if order.hold_id:
            try:
                await self.banking.release_hold(
                    bearer_token=bearer_token, hold_id=order.hold_id
                )
            except Exception:
                # The hold may already be released; we still cancel the order.
                pass

        updated = await self.repository.set_order_status(order_id, "cancelled")
        return updated or order

    async def list_orders_for_buyer(self, buyer_id: UUID) -> list[Order]:
        return await self.repository.list_orders_for_buyer(buyer_id)
