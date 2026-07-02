"""Схемы для регистрации, входа и обновления токенов."""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(
        min_length=8,
        max_length=72,  # ограничение алгоритма bcrypt
        description="Пароль, от 8 до 72 символов",
        examples=["strong-password-123"],
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(examples=["strong-password-123"])


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="Действующий refresh-токен")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
