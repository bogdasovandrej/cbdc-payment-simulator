"""Иерархия прикладных исключений.

Сервисы бросают эти исключения, а глобальный exception handler в main.py
превращает их в JSON-ответ единого формата:

    {"error": {"code": "...", "message": "..."}}
"""


class AppError(Exception):
    """Базовая ошибка приложения."""

    status_code: int = 500
    code: str = "internal_error"
    default_message: str = "Внутренняя ошибка сервера"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"
    default_message = "Некорректный запрос"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    default_message = "Требуется авторизация"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    default_message = "Доступ запрещён"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Ресурс не найден"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "Конфликт данных"


class GoneError(AppError):
    status_code = 410
    code = "gone"
    default_message = "Ресурс больше не доступен"


class BadGatewayError(AppError):
    status_code = 502
    code = "bad_gateway"
    default_message = "Платёжный провайдер недоступен, попробуйте позже"
