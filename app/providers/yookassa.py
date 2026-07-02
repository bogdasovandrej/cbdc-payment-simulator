"""Провайдер ЮKassa — реальное платёжное API.

Работает и с тестовым магазином ЮKassa (секретный ключ test_...):
API, статусы и страница оплаты те же, что в боевом режиме, но деньги
не списываются — оплата проверяется тестовой картой 5555 5555 5555 4477.

Документация: https://yookassa.ru/developers/api
"""
import logging
import uuid

import httpx
from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.exceptions import BadGatewayError
from app.models.payment import Payment, PaymentStatus
from app.providers.base import ProviderPaymentResult
from app.services import payment_processor

logger = logging.getLogger(__name__)

API_URL = "https://api.yookassa.ru/v3/payments"

# Статусы ЮKassa -> статусы нашего платежа
# pending             -> PROCESSING (ждём оплаты на странице ЮKassa)
# waiting_for_capture -> PAID (при capture=true не встречается, но на всякий)
# succeeded           -> PAID
# canceled            -> FAILED


class YooKassaProvider:
    def _auth(self) -> tuple[str, str]:
        settings = get_settings()
        return (settings.yookassa_shop_id, settings.yookassa_secret_key)

    def create(
        self, payment: Payment, background_tasks: BackgroundTasks
    ) -> ProviderPaymentResult:
        settings = get_settings()
        body = {
            "amount": {"value": f"{payment.amount:.2f}", "currency": "RUB"},
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url,
            },
            "description": f"Счёт #{payment.id} — симулятор цифрового рубля",
            "metadata": {"payment_id": payment.id},
        }
        try:
            response = httpx.post(
                API_URL,
                json=body,
                auth=self._auth(),
                # Idempotence-Key защищает от дублей при повторе запроса
                headers={"Idempotence-Key": str(uuid.uuid4())},
                timeout=15,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("YooKassa: не удалось создать платёж: %s", exc)
            raise BadGatewayError()

        data = response.json()
        return ProviderPaymentResult(
            external_id=data["id"],
            qr_payload=data["confirmation"]["confirmation_url"],
        )

    def refresh_status(self, payment: Payment) -> None:
        """Подтягивает статус из ЮKassa (pull-модель, без вебхуков).

        Ошибки сети не пробрасываем: клиент просто увидит прежний статус
        и обновит его следующим запросом.
        """
        if payment.status not in (PaymentStatus.CREATED, PaymentStatus.PROCESSING):
            return
        if not payment.external_id:
            return

        try:
            response = httpx.get(
                f"{API_URL}/{payment.external_id}", auth=self._auth(), timeout=15
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("YooKassa: не удалось получить статус: %s", exc)
            return

        external_status = response.json()["status"]
        if external_status == "pending":
            payment_processor.mark_processing(payment.id)
        elif external_status in ("succeeded", "waiting_for_capture"):
            payment_processor.mark_processing(payment.id)
            payment_processor.mark_paid(payment.id)
        elif external_status == "canceled":
            payment_processor.mark_processing(payment.id)
            payment_processor.mark_failed(payment.id)
