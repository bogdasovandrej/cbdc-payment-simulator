"""Добавляет payments.external_id — ID платежа во внешней платёжной системе.

Revision ID: 0002_external_id
Revises: 0001_initial
Create Date: 2026-07-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_external_id"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payments", sa.Column("external_id", sa.String(length=64), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("payments", "external_id")
