"""Платёжные провайдеры.

Приложение умеет работать с разными «внешними банками» через единый
интерфейс (см. base.PaymentProvider). Какой провайдер использовать,
задаёт настройка PAYMENT_PROVIDER:

* "mock"     — встроенная имитация платформы цифрового рубля (по умолчанию);
* "yookassa" — реальное API ЮKassa (подходит их тестовый магазин).
"""
from app.core.config import get_settings
from app.providers.base import PaymentProvider
from app.providers.mock import MockProvider
from app.providers.yookassa import YooKassaProvider

_mock_provider = MockProvider()
_yookassa_provider = YooKassaProvider()


def get_payment_provider() -> PaymentProvider:
    """Возвращает провайдера согласно настройке PAYMENT_PROVIDER."""
    if get_settings().payment_provider == "yookassa":
        return _yookassa_provider
    return _mock_provider
