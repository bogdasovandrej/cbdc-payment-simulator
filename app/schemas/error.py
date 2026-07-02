"""Единый формат ошибки API."""
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(description="Машиночитаемый код ошибки", examples=["not_found"])
    message: str = Field(
        description="Человекочитаемое описание", examples=["Платёж не найден"]
    )


class ErrorResponse(BaseModel):
    """Формат тела ответа для всех ошибок API."""

    error: ErrorDetail
