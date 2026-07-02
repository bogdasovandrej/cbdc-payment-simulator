"""Схемы профиля пользователя и баланса кошелька."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class BalanceResponse(BaseModel):
    wallet_id: int
    balance: Decimal
    currency: str
