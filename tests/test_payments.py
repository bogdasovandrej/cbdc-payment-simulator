"""Тесты платёжного процесса: создание, смена статусов, баланс, транзакции.

В тестовом окружении задержки Mock CBDC равны нулю, поэтому фоновая
обработка платежа завершается до возврата ответа TestClient — и уже
следующим запросом можно проверять финальный статус.
"""
from decimal import Decimal

from app.core.config import get_settings


def create_payment(client, headers, amount="100.50"):
    return client.post("/api/payments", json={"amount": amount}, headers=headers)


def test_create_payment_requires_auth(client):
    response = client.post("/api/payments", json={"amount": "100.00"})
    assert response.status_code == 401


def test_create_payment_returns_created_status(client, auth_headers):
    headers = auth_headers()
    response = create_payment(client, headers)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "CREATED"
    assert Decimal(str(data["amount"])) == Decimal("100.50")
    assert "id" in data


def test_negative_amount_returns_422(client, auth_headers):
    headers = auth_headers()
    response = create_payment(client, headers, amount="-5")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_zero_amount_returns_422(client, auth_headers):
    headers = auth_headers()
    response = create_payment(client, headers, amount="0")

    assert response.status_code == 422


def test_payment_becomes_paid_and_balance_updated(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    # Фоновая обработка Mock CBDC уже завершилась (задержки = 0)
    status_response = client.get(f"/api/payments/{payment_id}", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "PAID"

    balance_response = client.get("/api/user/balance", headers=headers)
    assert balance_response.status_code == 200
    balance = Decimal(str(balance_response.json()["balance"]))
    assert balance == Decimal("100.50")


def test_paid_payment_creates_deposit_transaction(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    response = client.get("/api/user/transactions", headers=headers)

    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 1
    assert transactions[0]["type"] == "DEPOSIT"
    assert transactions[0]["payment_id"] == payment_id
    assert Decimal(str(transactions[0]["amount"])) == Decimal("100.50")


def test_failed_payment_does_not_change_balance(client, auth_headers, monkeypatch):
    monkeypatch.setattr(get_settings(), "mock_fail_probability", 1.0)

    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    status_response = client.get(f"/api/payments/{payment_id}", headers=headers)
    assert status_response.json()["status"] == "FAILED"

    balance = Decimal(str(client.get("/api/user/balance", headers=headers).json()["balance"]))
    assert balance == Decimal("0")

    transactions = client.get("/api/user/transactions", headers=headers).json()
    assert transactions == []


def test_mock_status_reflects_final_state(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    response = client.get(f"/mock/status/{payment_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "PAID"


def test_get_unknown_payment_returns_404(client, auth_headers):
    headers = auth_headers()
    response = client.get("/api/payments/99999", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_foreign_payment_is_hidden(client, auth_headers):
    """Чужой платёж недоступен и выглядит как несуществующий (404)."""
    owner_headers = auth_headers(email="owner@example.com")
    payment_id = create_payment(client, owner_headers).json()["id"]

    other_headers = auth_headers(email="other@example.com")
    response = client.get(f"/api/payments/{payment_id}", headers=other_headers)

    assert response.status_code == 404


def test_list_payments_with_pagination(client, auth_headers):
    headers = auth_headers()
    for amount in ("10.00", "20.00", "30.00"):
        create_payment(client, headers, amount=amount)

    response = client.get("/api/payments?limit=2&offset=0", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    rest = client.get("/api/payments?limit=2&offset=2", headers=headers).json()
    assert len(rest["items"]) == 1


def test_multiple_payments_accumulate_balance(client, auth_headers):
    headers = auth_headers()
    create_payment(client, headers, amount="100.00")
    create_payment(client, headers, amount="250.50")

    balance = Decimal(str(client.get("/api/user/balance", headers=headers).json()["balance"]))
    assert balance == Decimal("350.50")

    transactions = client.get("/api/user/transactions", headers=headers).json()
    assert len(transactions) == 2
