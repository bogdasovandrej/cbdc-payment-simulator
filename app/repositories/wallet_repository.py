"""Репозиторий кошельков."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.wallet import Wallet


class WalletRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: int) -> Optional[Wallet]:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        return self.db.scalar(stmt)

    def create(self, user_id: int, currency: str) -> Wallet:
        wallet = Wallet(user_id=user_id, balance=Decimal("0"), currency=currency)
        self.db.add(wallet)
        self.db.flush()
        return wallet

    def add_to_balance(self, wallet: Wallet, amount: Decimal) -> Wallet:
        wallet.balance = wallet.balance + amount
        self.db.flush()
        return wallet
