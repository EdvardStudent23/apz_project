from fastapi import FastAPI, HTTPException, Header
from typing import List
from app.database import history_collection
from app.models import TransactionResponse

app = FastAPI(title="NanoBank History Service")

@app.get("/history", response_model=List[TransactionResponse])
async def get_history(user_id: str): 
    # В ідеалі user_id прийде від Gateway через заголовок, 
    # але поки що передаємо як query-параметр для тестів.
    
    # Шукаємо всі транзакції, де користувач був або відправником, або отримувачем
    cursor = history_collection.find({
        "$or": [
            {"sender_id": user_id},
            {"receiver_id": user_id}
        ]
    }).sort("timestamp", -1) # Сортуємо: найновіші зверху 

    history = await cursor.to_list(length=100) # Беремо останні 100 записів
    return history

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected"}