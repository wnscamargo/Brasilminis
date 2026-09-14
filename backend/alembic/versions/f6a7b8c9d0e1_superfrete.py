"""superfrete settings/shipments/events (aditiva)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06

Aditiva/não-destrutiva. NÃO remove nada do Melhor Envio.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "superfrete_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("environment", sa.String(), server_default="sandbox"),
        sa.Column("token_enc", sa.Text(), nullable=True),
        sa.Column("sender_name", sa.String(), server_default=""),
        sa.Column("sender_document", sa.String(), server_default=""),
        sa.Column("sender_phone", sa.String(), server_default=""),
        sa.Column("sender_email", sa.String(), server_default=""),
        sa.Column("sender_postal_code", sa.String(), server_default=""),
        sa.Column("sender_address", sa.String(), server_default=""),
        sa.Column("sender_number", sa.String(), server_default=""),
        sa.Column("sender_complement", sa.String(), server_default=""),
        sa.Column("sender_district", sa.String(), server_default=""),
        sa.Column("sender_city", sa.String(), server_default=""),
        sa.Column("sender_state", sa.String(), server_default=""),
        sa.Column("default_width", sa.Numeric(8, 2), nullable=True),
        sa.Column("default_height", sa.Numeric(8, 2), nullable=True),
        sa.Column("default_length", sa.Numeric(8, 2), nullable=True),
        sa.Column("default_weight", sa.Numeric(8, 3), nullable=True),
        sa.Column("enabled_services", JSONB(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.false()),
        sa.Column("status", sa.String(), server_default="not_configured"),
        sa.Column("last_test_at", sa.String(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )
    op.create_table(
        "superfrete_shipments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("order_id", sa.String(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("service_code", sa.String(), nullable=True),
        sa.Column("service_name", sa.String(), nullable=True),
        sa.Column("carrier_name", sa.String(), nullable=True),
        sa.Column("quoted_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("charged_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("estimated_days", sa.Integer(), nullable=True),
        sa.Column("label_status", sa.String(), nullable=True),
        sa.Column("label_external_id", sa.String(), nullable=True),
        sa.Column("label_url", sa.String(), nullable=True),
        sa.Column("tracking_code", sa.String(), nullable=True),
        sa.Column("tracking_url", sa.String(), nullable=True),
        sa.Column("shipment_status", sa.String(), server_default="PENDING"),
        sa.Column("raw_status", sa.String(), nullable=True),
        sa.Column("raw", JSONB(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("last_sync_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )
    op.create_index("ix_superfrete_shipments_order_id", "superfrete_shipments", ["order_id"])
    op.create_index("ix_superfrete_shipments_status", "superfrete_shipments", ["shipment_status"])
    op.create_table(
        "superfrete_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("external_event_id", sa.String(), nullable=True),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("shipment_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("payload_hash", sa.String(), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=True),
        sa.Column("processed", sa.Boolean(), server_default=sa.false()),
        sa.Column("processed_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_superfrete_events_hash", "superfrete_events", ["payload_hash"])


def downgrade() -> None:
    op.drop_index("ix_superfrete_events_hash", table_name="superfrete_events")
    op.drop_table("superfrete_events")
    op.drop_index("ix_superfrete_shipments_status", table_name="superfrete_shipments")
    op.drop_index("ix_superfrete_shipments_order_id", table_name="superfrete_shipments")
    op.drop_table("superfrete_shipments")
    op.drop_table("superfrete_settings")
