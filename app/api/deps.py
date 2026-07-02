"""Общие зависимости API: сессия БД и текущий пользователь."""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# auto_error=False, чтобы отсутствие токена обрабатывать самим
# и возвращать ошибку в едином формате.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Достаёт пользователя из access-токена в заголовке Authorization."""
    if credentials is None:
        raise UnauthorizedError("Требуется заголовок Authorization: Bearer <token>")

    try:
        payload = decode_token(credentials.credentials)
    except InvalidTokenError:
        raise UnauthorizedError("Токен просрочен или недействителен")

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise UnauthorizedError("Ожидался access-токен")

    user = UserRepository(db).get_by_id(int(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Пользователь не найден")

    return user
