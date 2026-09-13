"""category home fields + badges catalog

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06

Aditiva/não-destrutiva:
- adiciona icon/show_on_home/featured em categories (nullable/default);
- cria tabela badges (catálogo administrável de estilos).
Product.badges (JSONB) permanece como associação por texto (compatibilidade).
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("icon", sa.String(), nullable=True, server_default=""))
    op.add_column("categories", sa.Column("show_on_home", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("categories", sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "badges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("bg_color", sa.String(), nullable=True, server_default="#FFC107"),
        sa.Column("text_color", sa.String(), nullable=True, server_default="#111111"),
        sa.Column("icon", sa.String(), nullable=True, server_default=""),
        sa.Column("priority", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )
    op.create_index("ix_badges_text", "badges", ["text"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_badges_text", table_name="badges")
    op.drop_table("badges")
    op.drop_column("categories", "featured")
    op.drop_column("categories", "show_on_home")
    op.drop_column("categories", "icon")
