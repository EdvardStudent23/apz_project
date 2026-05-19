from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from neo4j import AsyncDriver


# ── Domain shapes ────────────────────────────────────────────────────────


@dataclass
class Product:
    id: UUID
    owner_id: UUID
    name: str
    description: str
    price: float
    currency: str
    status: str  # pending | approved | rejected
    moderation_note: str | None
    created_at: datetime


@dataclass
class Order:
    id: UUID
    product_id: UUID
    buyer_id: UUID
    hold_id: UUID | None
    amount: float
    currency: str
    status: str  # placed | cancelled
    created_at: datetime


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _product_from_row(row: dict[str, Any]) -> Product:
    return Product(
        id=UUID(row["id"]),
        owner_id=UUID(row["owner_id"]),
        name=row["name"],
        description=row.get("description") or "",
        price=float(row["price"]),
        currency=row["currency"],
        status=row["status"],
        moderation_note=row.get("moderation_note"),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _order_from_row(row: dict[str, Any]) -> Order:
    return Order(
        id=UUID(row["id"]),
        product_id=UUID(row["product_id"]),
        buyer_id=UUID(row["buyer_id"]),
        hold_id=UUID(row["hold_id"]) if row.get("hold_id") else None,
        amount=float(row["amount"]),
        currency=row["currency"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# ── Repository ────────────────────────────────────────────────────────────


class MarketRepository:
    def __init__(self, driver: AsyncDriver) -> None:
        self.driver = driver

    # --- products ---

    async def create_product(
        self,
        owner_id: UUID,
        name: str,
        description: str,
        price: float,
        currency: str,
    ) -> Product:
        product_id = uuid4()
        created = _now_iso()
        query = """
        MERGE (u:User {id: $owner_id})
        CREATE (p:Product {
            id: $id, owner_id: $owner_id, name: $name, description: $description,
            price: $price, currency: $currency, status: 'pending',
            moderation_note: null, created_at: $created_at
        })
        MERGE (u)-[:LISTED]->(p)
        RETURN p { .* } AS p
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                id=str(product_id),
                owner_id=str(owner_id),
                name=name,
                description=description,
                price=float(price),
                currency=currency,
                created_at=created,
            )
            record = await result.single()
        if not record:
            raise RuntimeError("product creation returned no row")
        return _product_from_row(dict(record["p"]))

    async def get_product(self, product_id: UUID) -> Product | None:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (p:Product {id: $id}) RETURN p { .* } AS p",
                id=str(product_id),
            )
            record = await result.single()
        if not record:
            return None
        return _product_from_row(dict(record["p"]))

    async def list_products_by_status(self, status: str) -> list[Product]:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (p:Product {status: $status}) "
                "RETURN p { .* } AS p ORDER BY p.created_at DESC",
                status=status,
            )
            rows = [dict(record["p"]) async for record in result]
        return [_product_from_row(r) for r in rows]

    async def list_products_for_owner(self, owner_id: UUID) -> list[Product]:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (p:Product {owner_id: $owner_id}) "
                "RETURN p { .* } AS p ORDER BY p.created_at DESC",
                owner_id=str(owner_id),
            )
            rows = [dict(record["p"]) async for record in result]
        return [_product_from_row(r) for r in rows]

    async def set_product_status(
        self,
        product_id: UUID,
        status: str,
        moderation_note: str | None = None,
    ) -> Product | None:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (p:Product {id: $id}) "
                "SET p.status = $status, p.moderation_note = $note "
                "RETURN p { .* } AS p",
                id=str(product_id),
                status=status,
                note=moderation_note,
            )
            record = await result.single()
        if not record:
            return None
        return _product_from_row(dict(record["p"]))

    # --- orders ---

    async def create_order(
        self,
        product_id: UUID,
        buyer_id: UUID,
        hold_id: UUID,
        amount: float,
        currency: str,
    ) -> Order:
        order_id = uuid4()
        created = _now_iso()
        query = """
        MATCH (p:Product {id: $product_id})
        MERGE (b:User {id: $buyer_id})
        CREATE (o:Order {
            id: $id, product_id: $product_id, buyer_id: $buyer_id,
            hold_id: $hold_id, amount: $amount, currency: $currency,
            status: 'placed', created_at: $created_at
        })
        MERGE (b)-[:ORDERED]->(o)
        MERGE (o)-[:FOR]->(p)
        RETURN o { .* } AS o
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                id=str(order_id),
                product_id=str(product_id),
                buyer_id=str(buyer_id),
                hold_id=str(hold_id),
                amount=float(amount),
                currency=currency,
                created_at=created,
            )
            record = await result.single()
        if not record:
            raise RuntimeError("order creation returned no row")
        return _order_from_row(dict(record["o"]))

    async def list_orders_for_buyer(self, buyer_id: UUID) -> list[Order]:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (o:Order {buyer_id: $buyer_id}) "
                "RETURN o { .* } AS o ORDER BY o.created_at DESC",
                buyer_id=str(buyer_id),
            )
            rows = [dict(record["o"]) async for record in result]
        return [_order_from_row(r) for r in rows]

    async def get_order(self, order_id: UUID) -> Order | None:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (o:Order {id: $id}) RETURN o { .* } AS o",
                id=str(order_id),
            )
            record = await result.single()
        if not record:
            return None
        return _order_from_row(dict(record["o"]))

    async def set_order_status(self, order_id: UUID, status: str) -> Order | None:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (o:Order {id: $id}) SET o.status = $status RETURN o { .* } AS o",
                id=str(order_id),
                status=status,
            )
            record = await result.single()
        if not record:
            return None
        return _order_from_row(dict(record["o"]))
