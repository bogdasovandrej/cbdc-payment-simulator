"""Эндпоинты аутентификации."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.error import ErrorResponse
from app.schemas.user import UserProfile
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создаёт пользователя и кошелёк цифрового рубля с нулевым балансом.",
    responses={
        409: {"model": ErrorResponse, "description": "Email уже зарегистрирован"},
        422: {"model": ErrorResponse, "description": "Некорректные данные"},
    },
)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> UserProfile:
    user = AuthService(db).register(email=body.email, password=body.password)
    return UserProfile.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Вход",
    description="Проверяет email/пароль и возвращает пару JWT-токенов.",
    responses={
        401: {"model": ErrorResponse, "description": "Неверный email или пароль"},
    },
)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    access_token, refresh_token = AuthService(db).login(
        email=body.email, password=body.password
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Обновление токенов",
    description="Выдаёт новую пару токенов по действующему refresh-токену.",
    responses={
        401: {"model": ErrorResponse, "description": "Refresh-токен недействителен"},
    },
)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    access_token, refresh_token = AuthService(db).refresh_tokens(body.refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)
