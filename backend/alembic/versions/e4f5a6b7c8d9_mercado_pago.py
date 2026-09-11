"""mercado pago: settings, payment snapshot, webhook events

Revision ID: e4f5a6b7c8d9
Revises: d2e3f4a5b6c7
Create Date: 2026-06-12 00:00:00.000000

Não-destrutiva.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for col, typ in [
        ("payment_provider", sa.String()),
        ("payment_external_id", sa.String()),
        ("payment_mp_id", sa.String()),
        ("payment_status_detail", sa.String()),
        ("payment_status_raw", sa.String()),
        ("payment_amount", sa.Numeric(12, 2)),
        ("payment_created_at", sa.String()),
        ("payment_approved_at", sa.String()),
        ("payment_idempotency_key", sa.String()),
    ]:
        op.add_column("orders", sa.Column(col, typ, nullable=True))
    op.create_index("ix_orders_payment_external_id", "orders", ["payment_external_id"])
    op.create_index("ix_orders_payment_mp_id", "orders", ["payment_mp_id"])

    op.create_table(
        "mp_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("environment", sa.String(), server_default="test"),
        sa.Column("public_key", sa.String(), nullable=True),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("webhook_secret_enc", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.false()),
        sa.Column("status", sa.String(), server_default="not_configured"),
        sa.Column("last_test_at", sa.String(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )

    op.create_table(
        "mp_webhook_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("data_id", sa.String(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("received_at", sa.String(), nullable=True),
    )
    op.create_index("ix_mp_webhook_data_id", "mp_webhook_events", ["data_id"])

    op.create_table(
        "payment_audit_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("detail", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_payment_audit_order_id", "payment_audit_logs", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_audit_order_id", table_name="payment_audit_logs")
    op.drop_table("payment_audit_logs")
    op.drop_index("ix_mp_webhook_data_id", table_name="mp_webhook_events")
    op.drop_table("mp_webhook_events")
    op.drop_table("mp_settings")
    op.drop_index("ix_orders_payment_mp_id", table_name="orders")
    op.drop_index("ix_orders_payment_external_id", table_name="orders")
    for col in ("payment_idempotency_key", "payment_approved_at", "payment_created_at",
                "payment_amount", "payment_status_raw", "payment_status_detail",
                "payment_mp_id", "payment_external_id", "payment_provider"):
        op.drop_column("orders", col)
