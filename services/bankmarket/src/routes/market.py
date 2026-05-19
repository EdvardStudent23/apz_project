from __future__ import annotations

from typing import Annotated
from uuid import UUID

from common.schemas import ApiResponse
from fastapi import APIRouter, Depends

from src.db.repository import Order, Product
from src.routes.common.deps import (
    AdminIdentity,
    BearerToken,
    CurrentIdentity,
    get_market_service,
)
from src.routes.schemas import (
    ModerationDecision,
    OrderCreate,
    OrderRead,
    ProductCreate,
    ProductRead,
)
from src.services.market import MarketService

router = APIRouter(prefix="/market", tags=["market"])


def _to_product(p: Product) -> ProductRead:
    return ProductRead(
        id=p.id,
        owner_id=p.owner_id,
        name=p.name,
        description=p.description,
        price=p.price,
        currency=p.currency,
        status=p.status,
        moderation_note=p.moderation_note,
        created_at=p.created_at,
    )


def _to_order(o: Order) -> OrderRead:
    return OrderRead(
        id=o.id,
        product_id=o.product_id,
        buyer_id=o.buyer_id,
        hold_id=o.hold_id,
        amount=o.amount,
        currency=o.currency,
        status=o.status,
        created_at=o.created_at,
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ── Products ─────────────────────────────────────────────────────────────


@router.post("/products", response_model=ApiResponse)
async def create_product(
    user: CurrentIdentity,
    data: ProductCreate,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    product = await service.create_product(
        owner_id=user.id,
        name=data.name,
        description=data.description,
        price=data.price,
        currency=data.currency,
    )
    return ApiResponse(status=True, response=_to_product(product))


@router.get("/products", response_model=ApiResponse)
async def list_approved(
    _user: CurrentIdentity,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    products = await service.list_approved()
    return ApiResponse(status=True, response=[_to_product(p) for p in products])


@router.get("/products/mine", response_model=ApiResponse)
async def list_mine(
    user: CurrentIdentity,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    products = await service.list_mine(user.id)
    return ApiResponse(status=True, response=[_to_product(p) for p in products])


@router.get("/products/pending", response_model=ApiResponse)
async def list_pending(
    _admin: AdminIdentity,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    products = await service.list_pending()
    return ApiResponse(status=True, response=[_to_product(p) for p in products])


@router.post("/products/{product_id}/moderate", response_model=ApiResponse)
async def moderate_product(
    _admin: AdminIdentity,
    product_id: UUID,
    data: ModerationDecision,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    product = await service.moderate(product_id, data.decision, data.note)
    return ApiResponse(status=True, response=_to_product(product))


# ── Orders ───────────────────────────────────────────────────────────────


@router.post("/orders", response_model=ApiResponse)
async def place_order(
    user: CurrentIdentity,
    token: BearerToken,
    data: OrderCreate,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    order = await service.place_order(
        product_id=data.product_id,
        buyer_id=user.id,
        buyer_account_id=data.account_id,
        bearer_token=token,
    )
    return ApiResponse(status=True, response=_to_order(order))


@router.get("/orders/mine", response_model=ApiResponse)
async def list_my_orders(
    user: CurrentIdentity,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    orders = await service.list_orders_for_buyer(user.id)
    return ApiResponse(status=True, response=[_to_order(o) for o in orders])


@router.post("/orders/{order_id}/cancel", response_model=ApiResponse)
async def cancel_order(
    user: CurrentIdentity,
    token: BearerToken,
    order_id: UUID,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> ApiResponse:
    order = await service.cancel_order(
        order_id=order_id, buyer_id=user.id, bearer_token=token
    )
    return ApiResponse(status=True, response=_to_order(order))
