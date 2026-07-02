"""Сервис платежей: создание, получение, список."""
from datetime import timedelta
from decimal import Decimal

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.payment import Payment
from app.models.user import User
from app.providers import get_payment_provider
from app.repositories.payment_repository import PaymentRepository
from app.repositories.qr_repository import QRCodeRepository
from app.utils.datetime_utils import utc_now


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.payments = PaymentRepository(db)
        self.qr_codes = QRCodeRepository(db)

    def create_payment(
        self, user: User, amount: Decimal, background_tasks: BackgroundTasks
    ) -> Payment:
        """Создаёт платёж в статусе CREATED и QR-код к нему.

        Платёж регистрируется у платёжного провайдера (mock или ЮKassa);
        provider возвращает содержимое QR-кода — для ЮKassa это настоящая
        ссылка на страницу оплаты. Если провайдер недоступен, транзакция
        откатывается и платёж не сохраняется.
        """
        settings = get_settings()

        payment = self.payments.create(user_id=user.id, amount=amount)
        result = get_payment_provider().create(payment, background_tasks)
        payment.external_id = result.external_id

        self.qr_codes.create(
            payment_id=payment.id,
            payload=result.qr_payload,
            expires_at=utc_now() + timedelta(minutes=settings.qr_ttl_minutes),
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_payment(self, user: User, payment_id: int) -> Payment:
        """Возвращает платёж пользователя с актуальным статусом.

        Чужой платёж намеренно отдаём как 404 (а не 403),
        чтобы не раскрывать существование чужих ресурсов.
        """
        payment = self.payments.get_by_id(payment_id)
        if payment is None or payment.user_id != user.id:
            raise NotFoundError("Платёж не найден")

        # У pull-провайдеров (ЮKassa) статус подтягивается при обращении.
        # Обновление идёт в отдельной сессии, поэтому перечитываем объект.
        if payment.external_id is not None:
            get_payment_provider().refresh_status(payment)
            self.db.refresh(payment)

        return payment

    def list_payments(
        self, user: User, limit: int, offset: int
    ) -> tuple[list[Payment], int]:
        items = self.payments.list_by_user(user.id, limit=limit, offset=offset)
        total = self.payments.count_by_user(user.id)
        return items, total
