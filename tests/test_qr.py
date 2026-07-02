"""Тесты QR-кодов."""
from datetime import datetime, timedelta, timezone

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def create_payment(client, headers, amount="100.50"):
    return client.post("/api/payments", json={"amount": amount}, headers=headers)


def test_get_qr_payload(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    response = client.get(f"/api/qr/{payment_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == payment_id
    assert f"payment_id={payment_id}" in data["payload"]
    assert data["payload"].startswith("cbdc://pay?")
    assert "expires_at" in data


def test_qr_image_is_png(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    response = client.get(f"/api/qr/{payment_id}/image", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(PNG_SIGNATURE)


def test_qr_requires_auth(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    response = client.get(f"/api/qr/{payment_id}")

    assert response.status_code == 401


def test_qr_for_unknown_payment_returns_404(client, auth_headers):
    headers = auth_headers()
    response = client.get("/api/qr/99999", headers=headers)

    assert response.status_code == 404


def test_expired_qr_returns_410(client, auth_headers):
    headers = auth_headers()
    payment_id = create_payment(client, headers).json()["id"]

    # Принудительно "просрочиваем" QR-код прямо в БД
    from app.db.session import SessionLocal
    from app.models.qr_code import QRCode

    with SessionLocal() as db:
        qr = db.query(QRCode).filter(QRCode.payment_id == payment_id).one()
        qr.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    response = client.get(f"/api/qr/{payment_id}", headers=headers)

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "gone"
