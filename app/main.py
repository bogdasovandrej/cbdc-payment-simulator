"""Точка входа FastAPI-приложения."""
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, payments, qr, user
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.mock_cbdc import router as mock_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Симулятор оплаты по QR-коду на базе API платформы цифрового рубля ЦБ РФ.\n\n"
        "Реальное API цифрового рубля недоступно публично, поэтому его роль "
        "выполняет встроенный Mock-сервис (`/mock/*`): он принимает платежи, "
        "эмулирует сетевые задержки и асинхронно меняет статусы платежей "
        "(CREATED → PROCESSING → PAID | FAILED)."
    ),
    version="1.0.0",
)


def _error_response(
    status_code: int, code: str, message: str, details=None
) -> JSONResponse:
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Прикладные ошибки (NotFoundError, ConflictError и т.д.)."""
    return _error_response(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Ошибки валидации Pydantic — приводим к единому формату."""
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "validation_error",
        "Некорректные данные запроса",
        details=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Стандартные HTTP-ошибки (например, 404 по несуществующему пути)."""
    return _error_response(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Последний рубеж: не отдаём наружу детали внутренних ошибок."""
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Внутренняя ошибка сервера",
    )


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(payments.router)
app.include_router(qr.router)
app.include_router(mock_router.router)


@app.get("/health", tags=["Служебные"], summary="Проверка работоспособности")
def health_check() -> dict:
    return {"status": "ok"}


# ---------- Веб-интерфейс ----------
# Одностраничный фронтенд (vanilla JS) поверх этого же API.

STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
