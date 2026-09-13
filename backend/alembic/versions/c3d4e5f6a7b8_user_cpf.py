"""users.cpf (dado pessoal, único, opcional para legados)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06

Não-destrutiva: adiciona coluna nullable + índice único. Legados permanecem NULL.
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("cpf", sa.String(), nullable=True))
    op.create_index("ix_users_cpf", "users", ["cpf"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_cpf", table_name="users")
    op.drop_column("users", "cpf")
