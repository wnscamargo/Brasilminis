"""customer soft delete + dashboard reset baseline

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06

Não-destrutiva:
- adiciona colunas de soft delete/anonimização em users (nullable);
- cria tabela dashboard_resets (marco de zeragem do Dashboard).
Nenhum dado existente é apagado ou recriado.
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.String(), nullable=True))
    op.add_column("users", sa.Column("deleted_by", sa.String(), nullable=True))
    op.add_column("users", sa.Column("delete_reason", sa.String(), nullable=True))
    op.add_column("users", sa.Column("anonymized_at", sa.String(), nullable=True))
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    op.create_table(
        "dashboard_resets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("reset_at", sa.String(), nullable=False),
        sa.Column("previous_reset_at", sa.String(), nullable=True),
        sa.Column("admin_id", sa.String(), nullable=True),
        sa.Column("admin_email", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_dashboard_resets_created_at", "dashboard_resets", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_dashboard_resets_created_at", table_name="dashboard_resets")
    op.drop_table("dashboard_resets")
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_column("users", "anonymized_at")
    op.drop_column("users", "delete_reason")
    op.drop_column("users", "deleted_by")
    op.drop_column("users", "deleted_at")
