"""Эндпоинты профиля пользователя, баланса и истории операций."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.transaction import TransactionResponse
from app.schemas.user import BalanceResponse, UserProfile
from app.services.user_service import UserService

router = APIRouter(prefix="/api/user", tags=["User"])

UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Требуется авторизация"}}


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="Профиль текущего пользователя",
    responses=UNAUTHORIZED,
)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(current_user)


@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="Баланс кошелька",
    responses=UNAUTHORIZED,
)
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BalanceResponse:
    wallet = UserService(db).get_wallet(current_user)
    return BalanceResponse(
        wallet_id=wallet.id, balance=wallet.balance, currency=wallet.currency
    )


@router.get(
    "/transactions",
    response_model=list[TransactionResponse],
    summary="История операций по кошельку",
    description="Транзакции отсортированы от новых к старым.",
    responses=UNAUTHORIZED,
)
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TransactionResponse]:
    transactions = UserService(db).get_transactions(current_user)
    return [TransactionResponse.model_validate(t) for t in transactions]
