"""Конфигурация приложения.

Все настройки читаются из переменных окружения (или файла .env).
Доступ к настройкам — только через get_settings(), чтобы объект
создавался один раз (lru_cache) и переиспользовался.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаемые из окружения / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Общие
    app_name: str = "CBDC QR Payment Simulator"
    debug: bool = False

    # База данных
    database_url: str = "postgresql+psycopg2://cbdc:cbdc@localhost:5432/cbdc"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Кошелёк
    wallet_currency: str = "RUB"

    # Платёжный провайдер: "mock" (встроенная имитация ЦБ)
    # или "yookassa" (реальное API ЮKassa, подходит их тестовый магазин)
    payment_provider: str = "mock"

    # ЮKassa (нужны только при payment_provider=yookassa)
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_return_url: str = "http://localhost:8000/"

    # QR-код
    qr_ttl_minutes: int = 15

    # Mock CBDC API (имитация внешней системы)
    mock_min_delay_seconds: float = 1.0
    mock_max_delay_seconds: float = 3.0
    mock_fail_probability: float = 0.2


@lru_cache
def get_settings() -> Settings:
    """Возвращает единственный экземпляр настроек."""
    return Settings()
