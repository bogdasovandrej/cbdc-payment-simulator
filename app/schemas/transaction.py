"""Схемы транзакций (история операций по кошельку)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TransactionType


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_id: Optional[int]
    amount: Decimal
    type: TransactionType
    created_at: datetime
