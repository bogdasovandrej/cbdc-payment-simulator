"""Утилиты для работы с датами."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Приводит datetime к таймзоне UTC.

    SQLite (используется в тестах) возвращает наивные datetime даже для
    колонок DateTime(timezone=True) — считаем такие значения временем в UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
