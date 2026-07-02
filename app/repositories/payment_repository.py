"""Репозиторий платежей."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        return self.db.get(Payment, payment_id)

    def create(self, user_id: int, amount: Decimal) -> Payment:
        payment = Payment(
            user_id=user_id, amount=amount, status=PaymentStatus.CREATED
        )
        self.db.add(payment)
        self.db.flush()
        return payment

    def list_by_user(self, user_id: int, limit: int, offset: int) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt).all())

    def count_by_user(self, user_id: int) -> int:
        stmt = select(func.count(Payment.id)).where(Payment.user_id == user_id)
        return self.db.scalar(stmt) or 0

    def set_status(self, payment: Payment, status: PaymentStatus) -> Payment:
        payment.status = status
        self.db.flush()
        return payment
