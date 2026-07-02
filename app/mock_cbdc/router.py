"""HTTP-эндпоинты Mock CBDC API.

Показывают, как выглядело бы внешнее API платформы цифрового рубля.
Основное приложение вызывает мок-сервис напрямую (in-process),
а эти эндпоинты полезны для демонстрации и ручной отладки в Swagger.
"""
from fastapi import APIRouter, BackgroundTasks, status

from app.core.exceptions import NotFoundError
from app.mock_cbdc.service import MockOperation, mock_cbdc
from app.schemas.error import ErrorResponse
from app.schemas.mock import MockOperationResponse, MockPayRequest

router = APIRouter(prefix="/mock", tags=["Mock CBDC API"])


def _to_response(operation: MockOperation) -> MockOperationResponse:
    return MockOperationResponse(
        payment_id=operation.payment_id,
        amount=operation.amount,
        status=operation.status,
        created_at=operation.created_at,
        updated_at=operation.updated_at,
    )


@router.post(
    "/pay",
    response_model=MockOperationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Принять платёж во «внешней» системе",
    description=(
        "Регистрирует платёж в имитируемой платформе цифрового рубля и "
        "запускает его фоновую обработку. Повторный вызов для того же "
        "payment_id идемпотентен — возвращает уже существующую операцию."
    ),
)
def mock_pay(
    body: MockPayRequest, background_tasks: BackgroundTasks
) -> MockOperationResponse:
    existing = mock_cbdc.get_operation(body.payment_id)
    if existing is not None:
        return _to_response(existing)

    operation = mock_cbdc.submit_payment(
        payment_id=body.payment_id, amount=body.amount
    )
    background_tasks.add_task(mock_cbdc.process_payment, body.payment_id)
    return _to_response(operation)


@router.get(
    "/status/{payment_id}",
    response_model=MockOperationResponse,
    summary="Статус операции во «внешней» системе",
    responses={
        404: {"model": ErrorResponse, "description": "Операция не найдена"},
    },
)
def mock_status(payment_id: int) -> MockOperationResponse:
    operation = mock_cbdc.get_operation(payment_id)
    if operation is None:
        raise NotFoundError("Операция не найдена во внешней системе")
    return _to_response(operation)
