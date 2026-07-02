"""Тесты регистрации, входа и обновления токенов."""
from tests.conftest import DEFAULT_EMAIL, DEFAULT_PASSWORD


def test_register_success(client, register_user):
    response = register_user()

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == DEFAULT_EMAIL
    assert "id" in data
    assert "created_at" in data
    # Пароль (даже хеш) не должен попадать в ответ
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_returns_409(client, register_user):
    register_user()
    response = register_user()

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "conflict"


def test_register_invalid_email_returns_422(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_register_short_password_returns_422(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "1234567"},
    )

    assert response.status_code == 422


def test_login_success(client, register_user):
    register_user()
    response = client.post(
        "/api/auth/login",
        json={"email": DEFAULT_EMAIL, "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, register_user):
    register_user()
    response = client.post(
        "/api/auth/login",
        json={"email": DEFAULT_EMAIL, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )

    assert response.status_code == 401


def test_profile_requires_token(client):
    response = client.get("/api/user/profile")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_profile_with_invalid_token_returns_401(client):
    response = client.get(
        "/api/user/profile", headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert response.status_code == 401


def test_profile_success(client, auth_headers):
    headers = auth_headers()
    response = client.get("/api/user/profile", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == DEFAULT_EMAIL


def test_refresh_returns_new_working_tokens(client, register_user):
    register_user()
    login_response = client.post(
        "/api/auth/login",
        json={"email": DEFAULT_EMAIL, "password": DEFAULT_PASSWORD},
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 200
    new_access = refresh_response.json()["access_token"]

    profile_response = client.get(
        "/api/user/profile", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert profile_response.status_code == 200


def test_refresh_with_access_token_returns_401(client, register_user):
    """Access-токен нельзя использовать вместо refresh-токена."""
    register_user()
    login_response = client.post(
        "/api/auth/login",
        json={"email": DEFAULT_EMAIL, "password": DEFAULT_PASSWORD},
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/refresh", json={"refresh_token": access_token}
    )

    assert response.status_code == 401


def test_access_endpoint_with_refresh_token_returns_401(client, register_user):
    """Refresh-токен нельзя использовать как access-токен."""
    register_user()
    login_response = client.post(
        "/api/auth/login",
        json={"email": DEFAULT_EMAIL, "password": DEFAULT_PASSWORD},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.get(
        "/api/user/profile", headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 401
