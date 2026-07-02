"""Engine, фабрика сессий и FastAPI-зависимость get_db."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    engine_kwargs: dict = {"pool_pre_ping": True}
    # SQLite используется только в тестах: разрешаем доступ из разных потоков
    # (фоновые задачи Mock CBDC работают в отдельном потоке).
    if settings.database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(settings.database_url, **engine_kwargs)


engine: Engine = _build_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI: выдаёт сессию и гарантированно закрывает её."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
