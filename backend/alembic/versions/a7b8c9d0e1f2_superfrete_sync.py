"""superfrete etapa C — sincronização automática (aditiva)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06

Aditiva/não-destrutiva. NÃO altera a f6a7b8c9d0e1. NÃO toca no Melhor Envio.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- superfrete_settings: suspensão global de sync ----
    op.add_column("superfrete_settings", sa.Column("sync_enabled", sa.Boolean(), server_default=sa.true()))
    op.add_column("superfrete_settings", sa.Column("sync_suspended", sa.Boolean(), server_default=sa.false()))
    op.add_column("superfrete_settings", sa.Column("sync_suspended_reason", sa.String(), nullable=True))
    op.add_column("superfrete_settings", sa.Column("sync_suspended_at", sa.String(), nullable=True))

    # ---- superfrete_shipments: controle individual de sync ----
    op.add_column("superfrete_shipments", sa.Column("sync_enabled", sa.Boolean(), server_default=sa.true()))
    op.add_column("superfrete_shipments", sa.Column("next_sync_at", sa.String(), nullable=True))
    op.add_column("superfrete_shipments", sa.Column("locked_at", sa.String(), nullable=True))
    op.add_column("superfrete_shipments", sa.Column("locked_by", sa.String(), nullable=True))
    op.add_column("superfrete_shipments", sa.Column("sync_attempts", sa.Integer(), server_default="0"))
    op.add_column("superfrete_shipments", sa.Column("version", sa.Integer(), server_default="0"))
    op.add_column("superfrete_shipments", sa.Column("last_status_at", sa.String(), nullable=True))
    op.create_index("ix_superfrete_shipments_next_sync_at", "superfrete_shipments", ["next_sync_at"])

    # ---- superfrete_events: timeline idempotente ----
    op.add_column("superfrete_events", sa.Column("source", sa.String(), nullable=True))
    op.add_column("superfrete_events", sa.Column("raw_status", sa.String(), nullable=True))
    op.add_column("superfrete_events", sa.Column("normalized_status", sa.String(), nullable=True))
    op.add_column("superfrete_events", sa.Column("description", sa.String(), nullable=True))
    op.add_column("superfrete_events", sa.Column("dedupe_key", sa.String(), nullable=True))
    op.add_column("superfrete_events", sa.Column("provider_event_at", sa.String(), nullable=True))
    op.add_column("superfrete_events", sa.Column("received_at", sa.String(), nullable=True))
    op.create_index("ix_superfrete_events_dedupe_key", "superfrete_events", ["dedupe_key"])
    op.create_unique_constraint("uq_superfrete_events_dedupe", "superfrete_events", ["dedupe_key"])

    # ---- superfrete_sync_runs: observabilidade ----
    op.create_table(
        "superfrete_sync_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("trigger", sa.String(), nullable=True),
        sa.Column("started_at", sa.String(), nullable=True),
        sa.Column("finished_at", sa.String(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("processed", sa.Integer(), server_default="0"),
        sa.Column("updated", sa.Integer(), server_default="0"),
        sa.Column("unchanged", sa.Integer(), server_default="0"),
        sa.Column("failed", sa.Integer(), server_default="0"),
        sa.Column("skipped", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
    )
    op.create_index("ix_superfrete_sync_runs_started", "superfrete_sync_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_superfrete_sync_runs_started", table_name="superfrete_sync_runs")
    op.drop_table("superfrete_sync_runs")
    op.drop_constraint("uq_superfrete_events_dedupe", "superfrete_events", type_="unique")
    op.drop_index("ix_superfrete_events_dedupe_key", table_name="superfrete_events")
    for col in ("received_at", "provider_event_at", "dedupe_key", "description",
                "normalized_status", "raw_status", "source"):
        op.drop_column("superfrete_events", col)
    op.drop_index("ix_superfrete_shipments_next_sync_at", table_name="superfrete_shipments")
    for col in ("last_status_at", "version", "sync_attempts", "locked_by", "locked_at",
                "next_sync_at", "sync_enabled"):
        op.drop_column("superfrete_shipments", col)
    for col in ("sync_suspended_at", "sync_suspended_reason", "sync_suspended", "sync_enabled"):
        op.drop_column("superfrete_settings", col)
