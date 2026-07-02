"""Репозиторий транзакций."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        wallet_id: int,
        amount: Decimal,
        type_: TransactionType,
        payment_id: Optional[int] = None,
    ) -> Transaction:
        transaction = Transaction(
            wallet_id=wallet_id,
            payment_id=payment_id,
            amount=amount,
            type=type_,
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def list_by_wallet(self, wallet_id: int) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        )
        return list(self.db.scalars(stmt).all())
