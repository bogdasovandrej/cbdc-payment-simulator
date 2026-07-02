"""Тесты провайдера ЮKassa.

HTTP-запросы к api.yookassa.ru подменяются фейками — тесты проверяют
нашу логику: регистрацию платежа, маппинг статусов, начисление на баланс.
"""
from decimal import Decimal

import pytest

from app.core.config import get_settings

FAKE_EXTERNAL_ID = "2e8b4a55-000f-5000-9000-1b5f12345678"
FAKE_CONFIRMATION_URL = (
    "https://yoomoney.ru/checkout/payments/v2/contract?orderId=" + FAKE_EXTERNAL_ID
)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=None
            )


@pytest.fixture
def yookassa_enabled(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "payment_provider", "yookassa")
    monkeypatch.setattr(settings, "yookassa_shop_id", "123456")
    monkeypatch.setattr(settings, "yookassa_secret_key", "test_fake_key")
    return settings


def make_created_response() -> FakeResponse:
    return FakeResponse(
        {
            "id": FAKE_EXTERNAL_ID,
            "status": "pending",
            "confirmation": {
                "type": "redirect",
                "confirmation_url": FAKE_CONFIRMATION_URL,
            },
        }
    )


def test_yookassa_payment_full_flow(client, auth_headers, yookassa_enabled, monkeypatch):
    """pending -> PROCESSING, succeeded -> PAID + пополнение баланса."""
    monkeypatch.setattr(
        "app.providers.yookassa.httpx.post",
        lambda *args, **kwargs: make_created_response(),
    )
    # Запрос QR-кода тоже сверяет статус с провайдером (через get_payment),
    # поэтому первое значение "pending" уйдёт на него.
    statuses = iter(["pending", "pending", "succeeded"])
    monkeypatch.setattr(
        "app.providers.yookassa.httpx.get",
        lambda *args, **kwargs: FakeResponse(
            {"id": FAKE_EXTERNAL_ID, "status": next(statuses)}
        ),
    )

    headers = auth_headers()
    response = client.post(
        "/api/payments", json={"amount": "500.00"}, headers=headers
    )
    assert response.status_code == 201
    assert response.json()["status"] == "CREATED"
    payment_id = response.json()["id"]

    # В QR-коде — настоящая ссылка на страницу оплаты ЮKassa
    qr = client.get(f"/api/qr/{payment_id}", headers=headers).json()
    assert qr["payload"] == FAKE_CONFIRMATION_URL

    # Первый запрос статуса: ЮKassa отвечает pending -> PROCESSING
    first = client.get(f"/api/payments/{payment_id}", headers=headers).json()
    assert first["status"] == "PROCESSING"

    # Второй запрос: succeeded -> PAID, баланс пополнен, транзакция создана
    second = client.get(f"/api/payments/{payment_id}", headers=headers).json()
    assert second["status"] == "PAID"

    balance = client.get("/api/user/balance", headers=headers).json()
    assert Decimal(str(balance["balance"])) == Decimal("500.00")

    transactions = client.get("/api/user/transactions", headers=headers).json()
    assert len(transactions) == 1
    assert transactions[0]["type"] == "DEPOSIT"


def test_yookassa_canceled_payment_fails(
    client, auth_headers, yookassa_enabled, monkeypatch
):
    monkeypatch.setattr(
        "app.providers.yookassa.httpx.post",
        lambda *args, **kwargs: make_created_response(),
    )
    monkeypatch.setattr(
        "app.providers.yookassa.httpx.get",
        lambda *args, **kwargs: FakeResponse(
            {"id": FAKE_EXTERNAL_ID, "status": "canceled"}
        ),
    )

    headers = auth_headers()
    payment_id = client.post(
        "/api/payments", json={"amount": "500.00"}, headers=headers
    ).json()["id"]

    status = client.get(f"/api/payments/{payment_id}", headers=headers).json()
    assert status["status"] == "FAILED"

    balance = client.get("/api/user/balance", headers=headers).json()
    assert Decimal(str(balance["balance"])) == Decimal("0")


def test_yookassa_unavailable_returns_502_and_no_payment(
    client, auth_headers, yookassa_enabled, monkeypatch
):
    """Если ЮKassa недоступна — 502, платёж не сохраняется."""
    import httpx

    def failing_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.providers.yookassa.httpx.post", failing_post)

    headers = auth_headers()
    response = client.post(
        "/api/payments", json={"amount": "500.00"}, headers=headers
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "bad_gateway"

    payments = client.get("/api/payments", headers=headers).json()
    assert payments["total"] == 0


def test_yookassa_status_error_keeps_previous_status(
    client, auth_headers, yookassa_enabled, monkeypatch
):
    """Ошибка сети при проверке статуса не ломает ответ клиенту."""
    import httpx

    monkeypatch.setattr(
        "app.providers.yookassa.httpx.post",
        lambda *args, **kwargs: make_created_response(),
    )

    def failing_get(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.providers.yookassa.httpx.get", failing_get)

    headers = auth_headers()
    payment_id = client.post(
        "/api/payments", json={"amount": "500.00"}, headers=headers
    ).json()["id"]

    response = client.get(f"/api/payments/{payment_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "CREATED"
