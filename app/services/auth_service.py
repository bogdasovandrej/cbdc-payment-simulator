"""Сервис регистрации и авторизации."""
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.wallets = WalletRepository(db)

    def register(self, email: str, password: str) -> User:
        """Создаёт пользователя и его кошелёк цифрового рубля."""
        if self.users.get_by_email(email) is not None:
            raise ConflictError("Пользователь с таким email уже зарегистрирован")

        user = self.users.create(
            email=email, hashed_password=hash_password(password)
        )
        self.wallets.create(
            user_id=user.id, currency=get_settings().wallet_currency
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> tuple[str, str]:
        """Проверяет учётные данные и выдаёт пару токенов (access, refresh)."""
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Неверный email или пароль")
        return create_access_token(user.id), create_refresh_token(user.id)

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Выдаёт новую пару токенов по действующему refresh-токену."""
        try:
            payload = decode_token(refresh_token)
        except InvalidTokenError:
            raise UnauthorizedError("Refresh-токен просрочен или недействителен")

        if payload.get("type") != TOKEN_TYPE_REFRESH:
            raise UnauthorizedError("Ожидался refresh-токен")

        user = self.users.get_by_id(int(payload["sub"]))
        if user is None:
            raise UnauthorizedError("Пользователь не найден")

        return create_access_token(user.id), create_refresh_token(user.id)
