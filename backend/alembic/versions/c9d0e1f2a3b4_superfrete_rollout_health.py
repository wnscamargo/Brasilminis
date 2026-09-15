"""superfrete etapa E — saúde do rollout / governança (aditiva)

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06

Aditiva/não-destrutiva. Head único. NÃO toca no Melhor Envio.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("superfrete_settings", sa.Column("rollout_min_orders", sa.Integer(), server_default="20"))
    op.add_column("superfrete_settings", sa.Column("rollout_alert_state", JSONB(), nullable=True))
    op.create_table(
        "superfrete_rollout_history",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("from_mode", sa.String(), nullable=True),
        sa.Column("to_mode", sa.String(), nullable=True),
        sa.Column("from_percentage", sa.Integer(), nullable=True),
        sa.Column("to_percentage", sa.Integer(), nullable=True),
        sa.Column("admin_id", sa.String(), nullable=True),
        sa.Column("admin_email", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("metrics_snapshot", JSONB(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_superfrete_rollout_history_created", "superfrete_rollout_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_superfrete_rollout_history_created", table_name="superfrete_rollout_history")
    op.drop_table("superfrete_rollout_history")
    op.drop_column("superfrete_settings", "rollout_alert_state")
    op.drop_column("superfrete_settings", "rollout_min_orders")
