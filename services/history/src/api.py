from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
from datetime import datetime
import sys

import aio_pika
from bank_logging import RequestIdMiddleware, configure_logging
from fastapi import FastAPI, Query
from common.schemas import ApiResponse

from src.middleware import ExceptionMiddleware
from src.settings import settings
from src.database import history_collection
from src.models import TransactionEvent, TransactionResponse


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            sys.stderr.write(f"[LISTENER] Payload: {json.dumps(payload)}\n")
            sys.stderr.flush()
            event_data = payload.get("payload", {})
            sys.stderr.write(f"[LISTENER] Event data: {json.dumps(event_data)}\n")
            sys.stderr.flush()

            history_record = {
                "sender_account_id": str(event_data.get("sender_account_id")),
                "receiver_account_id": str(event_data.get("receiver_account_id")),
                "sender_user_id": str(event_data.get("sender_user_id")),
                "receiver_user_id": str(event_data.get("receiver_user_id")),
                "sender_id": str(event_data.get("sender_account_id")),
                "receiver_id": str(event_data.get("receiver_account_id")),
                "amount": event_data.get("amount"),
                "currency": event_data.get("sender_currency"),
                "type": "transfer",
                "timestamp": datetime.utcnow()
            }
            sys.stderr.write(f"[LISTENER] Inserting history record: {json.dumps(history_record, default=str)}\n")
            sys.stderr.flush()

            result = await history_collection.insert_one(history_record)
            sys.stderr.write(f"[LISTENER] Inserted record with ID: {result.inserted_id}\n")
            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"[LISTENER] Error processing message: {e}\n")
            sys.stderr.flush()
            import traceback
            traceback.print_exc(file=sys.stderr)


async def start_listener(rabbitmq_url: str):
    while True:
        connection = None
        try:
            print(f"[LISTENER] Starting RabbitMQ listener with URL: {rabbitmq_url}")
            connection = await aio_pika.connect_robust(rabbitmq_url)
            print("[LISTENER] Connected to RabbitMQ")
            channel = await connection.channel()
            print("[LISTENER] Got channel")
            exchange = await channel.declare_exchange("core_banking.events", aio_pika.ExchangeType.TOPIC, durable=True)
            print("[LISTENER] Declared exchange")
            queue = await channel.declare_queue("history_queue", durable=True)
            print("[LISTENER] Declared queue")
            await queue.bind(exchange, "transaction.*")
            print("[LISTENER] Bound queue to exchange")

            print("[LISTENER] Starting message iterator...")
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    print(f"[LISTENER] Received message")
                    await process_message(message)
        except asyncio.CancelledError:
            print("[LISTENER] Listener task cancelled")
            break
        except Exception as e:
            print(f"[LISTENER] RabbitMQ listener error: {e}")
            print("[LISTENER] Retrying in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            if connection:
                try:
                    await connection.close()
                except Exception as e:
                    print(f"[LISTENER] Error closing connection: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.service_name)

    listener_task = asyncio.create_task(start_listener(settings.rabbitmq_url))

    yield

    listener_task.cancel()


app = FastAPI(title=settings.service_name, lifespan=lifespan)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(RequestIdMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/history", response_model=ApiResponse)
async def get_history(user_id: str = Query(None), account_id: str = Query(None)):
    """Get transaction history for a user or account."""
    try:
        if account_id:
            query = {"$or": [
                {"sender_account_id": account_id},
                {"receiver_account_id": account_id},
            ]}
        elif user_id:
            from uuid import UUID
            user_ids_to_try = [user_id]
            try:
                user_ids_to_try.append(str(UUID(int=int(user_id))))
            except (ValueError, TypeError):
                pass
            query = {"$or": [
                {"sender_user_id": {"$in": user_ids_to_try}},
                {"receiver_user_id": {"$in": user_ids_to_try}},
            ]}
        else:
            return ApiResponse(status=False, response="Missing user_id or account_id parameter")

        transactions = await history_collection.find(query).sort("timestamp", -1).to_list(100)

        return ApiResponse(
            status=True,
            response=[TransactionResponse(**t) for t in transactions]
        )
    except Exception as e:
        return ApiResponse(status=False, response=str(e))
