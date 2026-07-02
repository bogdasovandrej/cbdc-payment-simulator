"""Сервис платежей: создание, получение, список."""
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.payment import Payment
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.repositories.qr_repository import QRCodeRepository
from app.utils.datetime_utils import utc_now
from app.utils.qr_generator import build_qr_payload


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.payments = PaymentRepository(db)
        self.qr_codes = QRCodeRepository(db)

    def create_payment(self, user: User, amount: Decimal) -> Payment:
        """Создаёт платёж в статусе CREATED и QR-код к нему."""
        settings = get_settings()

        payment = self.payments.create(user_id=user.id, amount=amount)
        payload = build_qr_payload(
            payment_id=payment.id,
            amount=amount,
            currency=settings.wallet_currency,
        )
        self.qr_codes.create(
            payment_id=payment.id,
            payload=payload,
            expires_at=utc_now() + timedelta(minutes=settings.qr_ttl_minutes),
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_payment(self, user: User, payment_id: int) -> Payment:
        """Возвращает платёж пользователя.

        Чужой платёж намеренно отдаём как 404 (а не 403),
        чтобы не раскрывать существование чужих ресурсов.
        """
        payment = self.payments.get_by_id(payment_id)
        if payment is None or payment.user_id != user.id:
            raise NotFoundError("Платёж не найден")
        return payment

    def list_payments(
        self, user: User, limit: int, offset: int
    ) -> tuple[list[Payment], int]:
        items = self.payments.list_by_user(user.id, limit=limit, offset=offset)
        total = self.payments.count_by_user(user.id)
        return items, total
