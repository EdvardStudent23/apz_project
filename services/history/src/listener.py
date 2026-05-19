import asyncio
import json
import aio_pika
from datetime import datetime, timezone
from app.database import history_collection
from app.models import TransactionEvent

# Параметри підключення до RabbitMQ (Людина №1 має надати назву сервісу)
# У файлі app/listener.py
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():  # Automatically acknowledges (ACK) if there are no errors
        try:
            payload = json.loads(message.body.decode())
            print(f" [x] Received event: {payload}")

            # Validate data and add timestamp
            event_data = TransactionEvent(**payload)
            event_dict = event_data.dict()
            event_dict["timestamp"] = datetime.now(timezone.utc)

            # Save to MongoDB Replica Set
            await history_collection.insert_one(event_dict)
            print(" [v] Saved to history")

        except Exception as e:
            print(f" [!] Execution error: {e}")

async def main():
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # Declare queue (if it doesn't exist, it will be created)
    queue = await channel.declare_queue("history_queue", durable=True)

    print(' [*] Waiting for messages. Press CTRL+C to exit')

    # Start listening
    await queue.consume(process_message)

    # Keep the script running
    try:
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())