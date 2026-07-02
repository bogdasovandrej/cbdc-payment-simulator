"""Единый интерфейс платёжного провайдера."""
from dataclasses import dataclass
from typing import Optional, Protocol

from fastapi import BackgroundTasks

from app.models.payment import Payment


@dataclass
class ProviderPaymentResult:
    """Результат регистрации платежа во внешней системе."""

    external_id: Optional[str]  # ID платежа у провайдера (у мока нет)
    qr_payload: str  # что зашивается в QR-код (ссылка на оплату)


class PaymentProvider(Protocol):
    def create(
        self, payment: Payment, background_tasks: BackgroundTasks
    ) -> ProviderPaymentResult:
        """Регистрирует платёж во внешней системе.

        Вызывается при создании платежа, до commit — provider может
        бросить исключение, и тогда платёж не будет сохранён.
        """
        ...

    def refresh_status(self, payment: Payment) -> None:
        """Синхронизирует статус платежа с внешней системой.

        Вызывается при запросе статуса. Провайдеры, которые сами
        «пушат» статусы (mock), реализуют как no-op.
        """
        ...
