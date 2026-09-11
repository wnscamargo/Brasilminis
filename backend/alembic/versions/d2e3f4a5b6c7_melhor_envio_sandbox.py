"""melhor envio sandbox: logistics, shipping snapshot, tokens/sender/shipments

Revision ID: d2e3f4a5b6c7
Revises: c1f2a3b4d5e6
Create Date: 2026-06-11 00:00:00.000000

Não-destrutiva: adiciona colunas logísticas ao produto, snapshot de frete ao pedido
e as tabelas do Melhor Envio. Não reseta banco, não apaga dados.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1f2a3b4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # products: dados logísticos
    op.add_column("products", sa.Column("weight_kg", sa.Numeric(8, 3), nullable=True))
    op.add_column("products", sa.Column("width_cm", sa.Numeric(8, 2), nullable=True))
    op.add_column("products", sa.Column("height_cm", sa.Numeric(8, 2), nullable=True))
    op.add_column("products", sa.Column("length_cm", sa.Numeric(8, 2), nullable=True))
    op.add_column("products", sa.Column("sku", sa.String(), nullable=True))
    op.add_column("products", sa.Column("barcode", sa.String(), nullable=True))

    # orders: snapshot de frete
    op.add_column("orders", sa.Column("shipping_provider", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("shipping_service_id", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("shipping_service_name", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("shipping_company_id", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("shipping_company_name", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("shipping_price_customer", sa.Numeric(12, 2), nullable=True))
    op.add_column("orders", sa.Column("shipping_price_quoted", sa.Numeric(12, 2), nullable=True))
    op.add_column("orders", sa.Column("shipping_delivery_min", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("shipping_delivery_max", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("shipping_destination_postal_code", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("shipping_quote_snapshot", postgresql.JSONB(), nullable=True))
    op.add_column("orders", sa.Column("recipient_snapshot", postgresql.JSONB(), nullable=True))

    op.create_table(
        "melhor_envio_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("refresh_token_enc", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.String(), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("token_type", sa.String(), nullable=True),
        sa.Column("account_email", sa.String(), nullable=True),
        sa.Column("environment", sa.String(), server_default="sandbox"),
        sa.Column("pending_state", sa.String(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )

    op.create_table(
        "melhor_envio_sender",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), server_default=""),
        sa.Column("company", sa.String(), server_default=""),
        sa.Column("email", sa.String(), server_default=""),
        sa.Column("phone", sa.String(), server_default=""),
        sa.Column("document", sa.String(), server_default=""),
        sa.Column("state_register", sa.String(), server_default=""),
        sa.Column("postal_code", sa.String(), server_default=""),
        sa.Column("address", sa.String(), server_default=""),
        sa.Column("number", sa.String(), server_default=""),
        sa.Column("complement", sa.String(), server_default=""),
        sa.Column("district", sa.String(), server_default=""),
        sa.Column("city", sa.String(), server_default=""),
        sa.Column("state_abbr", sa.String(), server_default=""),
        sa.Column("updated_at", sa.String(), nullable=True),
    )

    op.create_table(
        "melhor_envio_shipments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("order_id", sa.String(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("cart_order_id", sa.String(), nullable=True),
        sa.Column("protocol", sa.String(), nullable=True),
        sa.Column("internal_status", sa.String(), server_default="pending"),
        sa.Column("external_status", sa.String(), nullable=True),
        sa.Column("tracking_code", sa.String(), nullable=True),
        sa.Column("label_url", sa.String(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("service_name", sa.String(), nullable=True),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("inserted_at", sa.String(), nullable=True),
        sa.Column("purchased_at", sa.String(), nullable=True),
        sa.Column("generated_at", sa.String(), nullable=True),
        sa.Column("posted_at", sa.String(), nullable=True),
        sa.Column("delivered_at", sa.String(), nullable=True),
        sa.Column("last_tracking_update_at", sa.String(), nullable=True),
        sa.Column("timeline", postgresql.JSONB(), nullable=True),
        sa.Column("raw", postgresql.JSONB(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )
    op.create_index("ix_me_shipments_order_id", "melhor_envio_shipments", ["order_id"])
    op.create_index("ix_me_shipments_cart_order_id", "melhor_envio_shipments", ["cart_order_id"])
    op.create_index("ix_me_shipments_internal_status", "melhor_envio_shipments", ["internal_status"])

    op.create_table(
        "shipping_quotes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("destination_postal_code", sa.String(), nullable=False),
        sa.Column("items", postgresql.JSONB(), nullable=True),
        sa.Column("volumes", postgresql.JSONB(), nullable=True),
        sa.Column("results", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("expires_at", sa.String(), nullable=False),
    )
    op.create_index("ix_shipping_quotes_user_id", "shipping_quotes", ["user_id"])

    op.create_table(
        "melhor_envio_webhook_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("event", sa.String(), nullable=True),
        sa.Column("order_ref", sa.String(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("received_at", sa.String(), nullable=True),
    )
    op.create_index("ix_me_webhook_order_ref", "melhor_envio_webhook_events", ["order_ref"])


def downgrade() -> None:
    op.drop_index("ix_me_webhook_order_ref", table_name="melhor_envio_webhook_events")
    op.drop_table("melhor_envio_webhook_events")
    op.drop_index("ix_shipping_quotes_user_id", table_name="shipping_quotes")
    op.drop_table("shipping_quotes")
    op.drop_index("ix_me_shipments_internal_status", table_name="melhor_envio_shipments")
    op.drop_index("ix_me_shipments_cart_order_id", table_name="melhor_envio_shipments")
    op.drop_index("ix_me_shipments_order_id", table_name="melhor_envio_shipments")
    op.drop_table("melhor_envio_shipments")
    op.drop_table("melhor_envio_sender")
    op.drop_table("melhor_envio_tokens")

    for col in ("recipient_snapshot", "shipping_quote_snapshot", "shipping_destination_postal_code",
                "shipping_delivery_max", "shipping_delivery_min", "shipping_price_quoted",
                "shipping_price_customer", "shipping_company_name", "shipping_company_id",
                "shipping_service_name", "shipping_service_id", "shipping_provider"):
        op.drop_column("orders", col)

    for col in ("barcode", "sku", "length_cm", "height_cm", "width_cm", "weight_kg"):
        op.drop_column("products", col)
