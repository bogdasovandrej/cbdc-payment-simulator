"""Репозиторий QR-кодов."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.qr_code import QRCode


class QRCodeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_payment_id(self, payment_id: int) -> Optional[QRCode]:
        stmt = select(QRCode).where(QRCode.payment_id == payment_id)
        return self.db.scalar(stmt)

    def create(self, payment_id: int, payload: str, expires_at: datetime) -> QRCode:
        qr = QRCode(payment_id=payment_id, payload=payload, expires_at=expires_at)
        self.db.add(qr)
        self.db.flush()
        return qr
