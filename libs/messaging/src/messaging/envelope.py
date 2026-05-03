from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime
    producer: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
