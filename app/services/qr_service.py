"""Сервис QR-кодов."""
from sqlalchemy.orm import Session

from app.core.exceptions import GoneError, NotFoundError
from app.models.qr_code import QRCode
from app.models.user import User
from app.repositories.qr_repository import QRCodeRepository
from app.services.payment_service import PaymentService
from app.utils.datetime_utils import ensure_utc, utc_now


class QRService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.qr_codes = QRCodeRepository(db)
        self.payment_service = PaymentService(db)

    def get_qr(self, user: User, payment_id: int) -> QRCode:
        """Возвращает QR-код платежа с проверкой владельца и срока действия."""
        # Проверка, что платёж существует и принадлежит пользователю
        self.payment_service.get_payment(user, payment_id)

        qr = self.qr_codes.get_by_payment_id(payment_id)
        if qr is None:
            raise NotFoundError("QR-код не найден")

        if ensure_utc(qr.expires_at) < utc_now():
            raise GoneError("Срок действия QR-кода истёк")

        return qr
