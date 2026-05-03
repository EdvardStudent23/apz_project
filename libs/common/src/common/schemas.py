from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    status: bool
    response: Any


class ErrorBody(BaseModel):
    code: str
    message: str
