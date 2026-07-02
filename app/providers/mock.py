"""Провайдер-имитация платформы цифрового рубля (по умолчанию)."""
from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.mock_cbdc.service import mock_cbdc
from app.models.payment import Payment
from app.providers.base import ProviderPaymentResult
from app.utils.qr_generator import build_qr_payload


class MockProvider:
    def create(
        self, payment: Payment, background_tasks: BackgroundTasks
    ) -> ProviderPaymentResult:
        # Регистрируем платёж во «внешней» системе; обработка — в фоне,
        # мок сам «уведомит» бэкенд о смене статусов.
        mock_cbdc.submit_payment(payment_id=payment.id, amount=payment.amount)
        background_tasks.add_task(mock_cbdc.process_payment, payment.id)

        payload = build_qr_payload(
            payment_id=payment.id,
            amount=payment.amount,
            currency=get_settings().wallet_currency,
        )
        return ProviderPaymentResult(external_id=None, qr_payload=payload)

    def refresh_status(self, payment: Payment) -> None:
        """Мок меняет статусы сам (push-модель) — синхронизация не нужна."""
