from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionEvent(BaseModel):
    sender_id: str
    receiver_id: str
    amount: float
    currency: str
    type: str  # наприклад, "transfer" або "market_purchase"
    timestamp: Optional[datetime] = None  # Ми додамо його самі


from pydantic import BaseModel
from datetime import datetime
from typing import List

class TransactionResponse(BaseModel):
    sender_id: str
    receiver_id: str
    amount: float
    currency: str
    type: str
    timestamp: datetime

    class Config:
        from_attributes = True