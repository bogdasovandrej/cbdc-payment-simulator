"""Обработчик уведомлений от Mock CBDC.

Функции этого модуля вызываются из фоновой задачи мок-сервиса
(в отдельном потоке), поэтому каждая открывает собственную сессию БД.

Переходы статусов строго контролируются:
CREATED -> PROCESSING -> PAID | FAILED.
"""
from app.db.session import SessionLocal
from app.models.payment import PaymentStatus
from app.models.transaction import TransactionType
from app.repositories.payment_repository import PaymentRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository


def mark_processing(payment_id: int) -> None:
    """Переводит платёж CREATED -> PROCESSING."""
    with SessionLocal() as db:
        payments = PaymentRepository(db)
        payment = payments.get_by_id(payment_id)
        if payment is None or payment.status != PaymentStatus.CREATED:
            return
        payments.set_status(payment, PaymentStatus.PROCESSING)
        db.commit()


def mark_paid(payment_id: int) -> None:
    """Переводит платёж PROCESSING -> PAID.

    Атомарно (в одной транзакции) обновляет баланс кошелька
    и создаёт запись Transaction.
    """
    with SessionLocal() as db:
        payments = PaymentRepository(db)
        wallets = WalletRepository(db)
        transactions = TransactionRepository(db)

        payment = payments.get_by_id(payment_id)
        if payment is None or payment.status != PaymentStatus.PROCESSING:
            return

        wallet = wallets.get_by_user_id(payment.user_id)
        if wallet is None:
            return

        payments.set_status(payment, PaymentStatus.PAID)
        wallets.add_to_balance(wallet, payment.amount)
        transactions.create(
            wallet_id=wallet.id,
            amount=payment.amount,
            type_=TransactionType.DEPOSIT,
            payment_id=payment.id,
        )
        db.commit()


def mark_failed(payment_id: int) -> None:
    """Переводит платёж PROCESSING -> FAILED. Баланс не меняется."""
    with SessionLocal() as db:
        payments = PaymentRepository(db)
        payment = payments.get_by_id(payment_id)
        if payment is None or payment.status != PaymentStatus.PROCESSING:
            return
        payments.set_status(payment, PaymentStatus.FAILED)
        db.commit()
