"""Аналитический отчёт по платежам (бонус-этап, аналитический трек).

Читает данные из PostgreSQL (или другой БД из DATABASE_URL) с помощью
pandas и печатает сводный отчёт: распределение по статусам, конверсию,
среднее время обработки и динамику по дням.

Запуск (из корня проекта, при поднятом docker-compose):

    pip install pandas
    python analytics/payments_report.py

По умолчанию подключается к postgresql+psycopg2://cbdc:cbdc@localhost:5432/cbdc,
URL можно переопределить переменной окружения DATABASE_URL.
"""
import os

import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://cbdc:cbdc@localhost:5432/cbdc"
)


def load_payments(engine) -> pd.DataFrame:
    query = """
        SELECT id, user_id, amount, status, created_at, updated_at
        FROM payments
    """
    return pd.read_sql(query, engine)


def print_status_distribution(payments: pd.DataFrame) -> None:
    print("\n=== Распределение платежей по статусам ===")
    distribution = payments["status"].value_counts()
    share = (100 * distribution / len(payments)).round(2)
    report = pd.DataFrame({"count": distribution, "share_%": share})
    print(report.to_string())


def print_conversion(payments: pd.DataFrame) -> None:
    print("\n=== Конверсия в успешные платежи ===")
    finished = payments[payments["status"].isin(["PAID", "FAILED"])]
    if finished.empty:
        print("Завершённых платежей пока нет")
        return
    paid_count = int((finished["status"] == "PAID").sum())
    conversion = 100 * paid_count / len(finished)
    print(f"Завершено платежей: {len(finished)}")
    print(f"Из них успешных:   {paid_count}")
    print(f"Конверсия:         {conversion:.2f}%")


def print_processing_time(payments: pd.DataFrame) -> None:
    print("\n=== Среднее время обработки (сек) ===")
    finished = payments[payments["status"].isin(["PAID", "FAILED"])].copy()
    if finished.empty:
        print("Завершённых платежей пока нет")
        return
    finished["processing_seconds"] = (
        finished["updated_at"] - finished["created_at"]
    ).dt.total_seconds()
    print(
        finished.groupby("status")["processing_seconds"]
        .agg(["count", "mean", "min", "max"])
        .round(2)
        .to_string()
    )


def print_daily_dynamics(payments: pd.DataFrame) -> None:
    print("\n=== Динамика по дням ===")
    df = payments.copy()
    df["day"] = pd.to_datetime(df["created_at"]).dt.date
    df["paid_amount"] = df["amount"].where(df["status"] == "PAID", 0)
    daily = df.groupby("day").agg(
        payments_count=("id", "count"),
        paid_turnover=("paid_amount", "sum"),
    )
    print(daily.to_string())


def main() -> None:
    engine = create_engine(DATABASE_URL)
    payments = load_payments(engine)

    if payments.empty:
        print("В базе пока нет платежей — создайте несколько через API.")
        return

    print(f"Всего платежей в базе: {len(payments)}")
    print_status_distribution(payments)
    print_conversion(payments)
    print_processing_time(payments)
    print_daily_dynamics(payments)


if __name__ == "__main__":
    main()
