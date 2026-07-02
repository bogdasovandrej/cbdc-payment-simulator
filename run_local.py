"""Локальный запуск без Docker (SQLite вместо PostgreSQL).

    python run_local.py

Что делает:
1. Настраивает окружение: SQLite-база local_dev.db в корне проекта.
2. Применяет миграции Alembic.
3. Запускает сервер на http://127.0.0.1:8000 (интерфейс — на этой же
   странице, Swagger — на /docs).

Для «боевого» запуска с PostgreSQL используйте docker-compose up --build.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

os.environ.setdefault(
    "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'local_dev.db').as_posix()}"
)
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret")


def main() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    command.upgrade(alembic_cfg, "head")

    import uvicorn

    print()
    print("  Интерфейс:  http://127.0.0.1:8000")
    print("  Swagger:    http://127.0.0.1:8000/docs")
    print()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
