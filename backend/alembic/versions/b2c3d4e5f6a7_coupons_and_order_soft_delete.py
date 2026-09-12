"""discount coupons (extended) + order soft delete + admin audit

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06

Não-destrutiva: só adiciona colunas/tabelas. Nada é apagado.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # coupons: novos campos
    c = "coupons"
    op.add_column(c, sa.Column("max_discount", sa.Numeric(12, 2), nullable=True))
    op.add_column(c, sa.Column("starts_at", sa.String(), nullable=True))
    op.add_column(c, sa.Column("expires_at", sa.String(), nullable=True))
    op.add_column(c, sa.Column("usage_limit", sa.Integer(), nullable=True))
    op.add_column(c, sa.Column("per_user_limit", sa.Integer(), nullable=True))
    op.add_column(c, sa.Column("used_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column(c, sa.Column("first_purchase_only", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column(c, sa.Column("free_shipping", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column(c, sa.Column("allow_stacking", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column(c, sa.Column("scope_type", sa.String(), nullable=True, server_default="all"))
    op.add_column(c, sa.Column("scope_category_ids", JSONB(), nullable=True, server_default="[]"))
    op.add_column(c, sa.Column("scope_product_ids", JSONB(), nullable=True, server_default="[]"))
    op.add_column(c, sa.Column("created_at", sa.String(), nullable=True))
    op.add_column(c, sa.Column("updated_at", sa.String(), nullable=True))

    # orders: snapshot do cupom + soft delete
    op.add_column("orders", sa.Column("coupon_snapshot", JSONB(), nullable=True))
    op.add_column("orders", sa.Column("deleted_at", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("deleted_by", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("delete_reason", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("stock_returned", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.create_index("ix_orders_deleted_at", "orders", ["deleted_at"])

    # coupon_redemptions
    op.create_table(
        "coupon_redemptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("coupon_code", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_coupon_redemptions_coupon_code", "coupon_redemptions", ["coupon_code"])
    op.create_index("ix_coupon_redemptions_user_id", "coupon_redemptions", ["user_id"])

    # admin_audit_logs
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("admin_id", sa.String(), nullable=True),
        sa.Column("admin_email", sa.String(), nullable=True),
        sa.Column("detail", JSONB(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_admin_audit_logs_event", "admin_audit_logs", ["event"])
    op.create_index("ix_admin_audit_logs_order_id", "admin_audit_logs", ["order_id"])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_index("ix_coupon_redemptions_user_id", table_name="coupon_redemptions")
    op.drop_index("ix_coupon_redemptions_coupon_code", table_name="coupon_redemptions")
    op.drop_table("coupon_redemptions")
    op.drop_index("ix_orders_deleted_at", table_name="orders")
    for col in ("stock_returned", "delete_reason", "deleted_by", "deleted_at", "coupon_snapshot"):
        op.drop_column("orders", col)
    for col in ("updated_at", "created_at", "scope_product_ids", "scope_category_ids", "scope_type",
                "allow_stacking", "free_shipping", "first_purchase_only", "used_count",
                "per_user_limit", "usage_limit", "expires_at", "starts_at", "max_discount"):
        op.drop_column("coupons", col)
