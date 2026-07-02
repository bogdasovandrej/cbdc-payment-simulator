"""Генерация QR-кодов."""
import io
from decimal import Decimal

import qrcode


def build_qr_payload(payment_id: int, amount: Decimal, currency: str) -> str:
    """Формирует строку-полезную нагрузку QR-кода.

    Формат условный, стилизованный под платёжную ссылку цифрового рубля.
    """
    return f"cbdc://pay?payment_id={payment_id}&amount={amount}&currency={currency}"


def generate_qr_png(payload: str) -> bytes:
    """Рендерит payload в PNG-изображение QR-кода."""
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
