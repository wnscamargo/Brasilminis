"""site: institutional content + social links (JSONB)

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-06

Evolui site_settings com conteúdo institucional e redes sociais (JSONB).
Não-destrutiva: não apaga nenhuma configuração existente.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "a1b2c3d4e5f6"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("site_settings", sa.Column("institutional_content", JSONB(), nullable=True, server_default="{}"))
    op.add_column("site_settings", sa.Column("social_links", JSONB(), nullable=True, server_default="{}"))


def downgrade() -> None:
    op.drop_column("site_settings", "social_links")
    op.drop_column("site_settings", "institutional_content")
