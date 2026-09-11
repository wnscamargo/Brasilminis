"""integrations hub: melhor envio operational credentials in DB

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-06

Move das credenciais operacionais do Melhor Envio (client_id/secret/redirect)
do .env para o banco (secret cifrado). Não-destrutiva.
"""
from alembic import op
import sqlalchemy as sa

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("melhor_envio_tokens", sa.Column("client_id", sa.String(), nullable=True))
    op.add_column("melhor_envio_tokens", sa.Column("client_secret_enc", sa.Text(), nullable=True))
    op.add_column("melhor_envio_tokens", sa.Column("redirect_uri", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("melhor_envio_tokens", "redirect_uri")
    op.drop_column("melhor_envio_tokens", "client_secret_enc")
    op.drop_column("melhor_envio_tokens", "client_id")
