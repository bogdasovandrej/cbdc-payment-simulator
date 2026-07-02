"""Имитация внешнего API платформы цифрового рубля.

Реальное API недоступно публично, поэтому его роль выполняет этот сервис:

* принимает платёж (submit_payment) — как будто платёж ушёл во внешнюю систему;
* хранит собственный реестр операций (in-memory) со статусами
  ACCEPTED -> PROCESSING -> PAID | FAILED;
* в фоновой задаче (process_payment) эмулирует сетевые задержки
  (случайный sleep) и вероятность отказа платежа;
* «уведомляет» наш бэкенд о смене статуса через функции
  app.services.payment_processor.
"""
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.core.config import get_settings
from app.services import payment_processor
from app.utils.datetime_utils import utc_now

STATUS_ACCEPTED = "ACCEPTED"
STATUS_PROCESSING = "PROCESSING"
STATUS_PAID = "PAID"
STATUS_FAILED = "FAILED"


@dataclass
class MockOperation:
    """Операция в «внешней» системе цифрового рубля."""

    payment_id: int
    amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class MockCBDCService:
    def __init__(self) -> None:
        self._operations: dict[int, MockOperation] = {}
        self._lock = threading.Lock()

    def submit_payment(self, payment_id: int, amount: Decimal) -> MockOperation:
        """Регистрирует платёж во «внешней» системе (идемпотентно)."""
        with self._lock:
            operation = self._operations.get(payment_id)
            if operation is not None:
                return operation
            now = utc_now()
            operation = MockOperation(
                payment_id=payment_id,
                amount=amount,
                status=STATUS_ACCEPTED,
                created_at=now,
                updated_at=now,
            )
            self._operations[payment_id] = operation
            return operation

    def get_operation(self, payment_id: int) -> "MockOperation | None":
        return self._operations.get(payment_id)

    def process_payment(self, payment_id: int) -> None:
        """Фоновая обработка платежа.

        Запускается через BackgroundTasks после создания платежа:
        эмулирует задержку сети, переводит платёж в PROCESSING,
        затем с настраиваемой вероятностью завершает его как FAILED
        или как PAID.
        """
        settings = get_settings()

        operation = self.get_operation(payment_id)
        if operation is None or operation.status != STATUS_ACCEPTED:
            return

        self._sleep_random()  # задержка сети до подтверждения приёма
        self._set_status(operation, STATUS_PROCESSING)
        payment_processor.mark_processing(payment_id)

        self._sleep_random()  # время «обработки» во внешней системе
        if random.random() < settings.mock_fail_probability:
            self._set_status(operation, STATUS_FAILED)
            payment_processor.mark_failed(payment_id)
        else:
            self._set_status(operation, STATUS_PAID)
            payment_processor.mark_paid(payment_id)

    def reset(self) -> None:
        """Очищает реестр операций (используется в тестах)."""
        with self._lock:
            self._operations.clear()

    def _set_status(self, operation: MockOperation, status: str) -> None:
        with self._lock:
            operation.status = status
            operation.updated_at = utc_now()

    @staticmethod
    def _sleep_random() -> None:
        settings = get_settings()
        delay = random.uniform(
            settings.mock_min_delay_seconds, settings.mock_max_delay_seconds
        )
        if delay > 0:
            time.sleep(delay)


# Единственный экземпляр «внешней системы» на всё приложение
mock_cbdc = MockCBDCService()
