"""Схемы QR-кода."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QRCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    payload: str = Field(
        description="Строка, зашитая в QR-код",
        examples=["cbdc://pay?payment_id=1&amount=1500.00&currency=RUB"],
    )
    expires_at: datetime
