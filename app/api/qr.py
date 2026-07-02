"""Эндпоинты QR-кодов."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.qr import QRCodeResponse
from app.services.qr_service import QRService
from app.utils.qr_generator import generate_qr_png

router = APIRouter(prefix="/api/qr", tags=["QR"])

QR_ERRORS = {
    401: {"model": ErrorResponse, "description": "Требуется авторизация"},
    404: {"model": ErrorResponse, "description": "Платёж или QR-код не найден"},
    410: {"model": ErrorResponse, "description": "Срок действия QR-кода истёк"},
}


@router.get(
    "/{payment_id}",
    response_model=QRCodeResponse,
    summary="Данные QR-кода платежа",
    responses=QR_ERRORS,
)
def get_qr(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QRCodeResponse:
    qr = QRService(db).get_qr(user=current_user, payment_id=payment_id)
    return QRCodeResponse.model_validate(qr)


@router.get(
    "/{payment_id}/image",
    summary="PNG-изображение QR-кода",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}, "description": "QR-код в формате PNG"},
        **QR_ERRORS,
    },
)
def get_qr_image(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    qr = QRService(db).get_qr(user=current_user, payment_id=payment_id)
    png_bytes = generate_qr_png(qr.payload)
    return Response(content=png_bytes, media_type="image/png")
