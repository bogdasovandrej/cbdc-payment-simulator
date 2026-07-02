"""Схемы Mock CBDC API (имитация внешней системы цифрового рубля)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MockPayRequest(BaseModel):
    payment_id: int = Field(description="ID платежа в нашей системе", examples=[1])
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2, examples=["1500.00"])


class MockOperationResponse(BaseModel):
    payment_id: int
    amount: Decimal
    status: str = Field(
        description="Статус операции во внешней системе",
        examples=["ACCEPTED", "PROCESSING", "PAID", "FAILED"],
    )
    created_at: datetime
    updated_at: datetime
