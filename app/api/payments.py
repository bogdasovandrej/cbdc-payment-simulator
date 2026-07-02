"""Эндпоинты платежей."""
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["Payments"])

UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Требуется авторизация"}}


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать платёж",
    description=(
        "Создаёт платёж в статусе CREATED и QR-код к нему, затем отправляет "
        "платёж в Mock CBDC. Дальше статус меняется асинхронно: "
        "CREATED → PROCESSING → PAID | FAILED. Актуальный статус — "
        "через GET /api/payments/{id}."
    ),
    responses={
        **UNAUTHORIZED,
        422: {"model": ErrorResponse, "description": "Некорректная сумма"},
    },
)
def create_payment(
    body: PaymentCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    payment = PaymentService(db).create_payment(
        user=current_user, amount=body.amount, background_tasks=background_tasks
    )
    return PaymentResponse.model_validate(payment)


@router.get(
    "",
    response_model=PaymentListResponse,
    summary="Список платежей пользователя",
    description="Платежи отсортированы от новых к старым, есть пагинация.",
    responses=UNAUTHORIZED,
)
def list_payments(
    limit: int = Query(20, ge=1, le=100, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение от начала списка"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentListResponse:
    items, total = PaymentService(db).list_payments(
        user=current_user, limit=limit, offset=offset
    )
    return PaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Статус платежа",
    responses={
        **UNAUTHORIZED,
        404: {"model": ErrorResponse, "description": "Платёж не найден"},
    },
)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    payment = PaymentService(db).get_payment(user=current_user, payment_id=payment_id)
    return PaymentResponse.model_validate(payment)
