"""SQLAlchemy-модели.

Импортируем все модели здесь, чтобы они регистрировались в Base.metadata —
это нужно Alembic (автогенерация/сравнение схемы) и Base.metadata.create_all
в тестах.
"""
from app.models.payment import Payment, PaymentStatus
from app.models.qr_code import QRCode
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.wallet import Wallet

__all__ = [
    "Payment",
    "PaymentStatus",
    "QRCode",
    "Transaction",
    "TransactionType",
    "User",
    "Wallet",
]
