"""Декларативная база для всех SQLAlchemy-моделей."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс моделей. Metadata этого класса использует Alembic."""
