"""Общие фикстуры тестов.

Тесты используют SQLite вместо PostgreSQL, а у Mock CBDC отключаются
задержки и случайность (вероятность отказа = 0), чтобы тесты были
быстрыми и детерминированными.

ВАЖНО: переменные окружения выставляются ДО импорта приложения,
потому что настройки читаются один раз при создании Settings.
"""
import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_app.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["MOCK_MIN_DELAY_SECONDS"] = "0"
os.environ["MOCK_MAX_DELAY_SECONDS"] = "0"
os.environ["MOCK_FAIL_PROBABILITY"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.mock_cbdc.service import mock_cbdc  # noqa: E402

DEFAULT_EMAIL = "user@example.com"
DEFAULT_PASSWORD = "password123"


@pytest.fixture(autouse=True)
def clean_state():
    """Перед каждым тестом: чистая схема БД и пустой реестр мок-сервиса."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    mock_cbdc.reset()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def register_user(client):
    """Фабрика: регистрирует пользователя и возвращает ответ API."""

    def _register(email: str = DEFAULT_EMAIL, password: str = DEFAULT_PASSWORD):
        return client.post(
            "/api/auth/register", json={"email": email, "password": password}
        )

    return _register


@pytest.fixture
def auth_headers(client, register_user):
    """Фабрика: регистрирует пользователя, логинится и возвращает заголовки."""

    def _make(email: str = DEFAULT_EMAIL, password: str = DEFAULT_PASSWORD):
        register_user(email=email, password=password)
        response = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
