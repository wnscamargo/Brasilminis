"""superfrete etapa D — rollout de produção controlada (aditiva)

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06

Aditiva/não-destrutiva. Head único. NÃO toca no Melhor Envio.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("superfrete_settings", sa.Column("rollout_mode", sa.String(), server_default="ENABLED"))
    op.add_column("superfrete_settings", sa.Column("rollout_percentage", sa.Integer(), server_default="0"))
    op.add_column("superfrete_settings", sa.Column("test_order_id", sa.String(), nullable=True))
    op.add_column("superfrete_settings", sa.Column("controlled_test_state", JSONB(), nullable=True))
    op.add_column("orders", sa.Column("is_test_order", sa.Boolean(), server_default=sa.false()))
    op.create_index("ix_orders_is_test_order", "orders", ["is_test_order"])


def downgrade() -> None:
    op.drop_index("ix_orders_is_test_order", table_name="orders")
    op.drop_column("orders", "is_test_order")
    for col in ("controlled_test_state", "test_order_id", "rollout_percentage", "rollout_mode"):
        op.drop_column("superfrete_settings", col)
