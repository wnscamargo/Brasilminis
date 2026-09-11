"""catalog hierarchy, cost/cmv, product images

Revision ID: c1f2a3b4d5e6
Revises: 455b5d4bbb3e
Create Date: 2026-06-10 00:00:00.000000

Evolução estrutural NÃO-destrutiva:
- Categorias hierárquicas (parent_id, is_active, sort_order, timestamps).
- Custo do produto (cost_price) + preços/valores monetários -> Numeric(12,2).
- Tabelas product_images e product_cost_history.
- Migração de dados: group -> categoria principal; categorias atuais -> subcategorias;
  vínculo dos produtos; product_images a partir do array images existente.
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "c1f2a3b4d5e6"
down_revision: Union[str, None] = "455b5d4bbb3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GROUP_LABELS = {
    "miniaturas": "Miniaturas",
    "colecionaveis": "Colecionáveis",
    "acessorios": "Acessórios",
    "vestuario": "Vestuário",
    "presentes": "Presentes",
}
GROUP_ORDER = ["miniaturas", "colecionaveis", "acessorios", "vestuario", "presentes"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upgrade() -> None:
    # ---------- Schema: categories ----------
    op.add_column("categories", sa.Column("parent_id", sa.String(), nullable=True))
    op.add_column("categories", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("categories", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("categories", sa.Column("created_at", sa.String(), nullable=True))
    op.add_column("categories", sa.Column("updated_at", sa.String(), nullable=True))
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_foreign_key("fk_categories_parent", "categories", "categories", ["parent_id"], ["id"])

    # ---------- Schema: products ----------
    op.alter_column("products", "price", type_=sa.Numeric(12, 2),
                    existing_type=sa.Float(), postgresql_using="price::numeric(12,2)")
    op.alter_column("products", "compare_at_price", type_=sa.Numeric(12, 2),
                    existing_type=sa.Float(), existing_nullable=True,
                    postgresql_using="compare_at_price::numeric(12,2)")
    op.alter_column("products", "rating", type_=sa.Numeric(3, 2),
                    existing_type=sa.Float(), postgresql_using="rating::numeric(3,2)")
    op.add_column("products", sa.Column("cost_price", sa.Numeric(12, 2), nullable=True))
    op.add_column("products", sa.Column("main_category_id", sa.String(), nullable=True))
    op.add_column("products", sa.Column("subcategory_id", sa.String(), nullable=True))
    op.create_index("ix_products_main_category_id", "products", ["main_category_id"])
    op.create_index("ix_products_subcategory_id", "products", ["subcategory_id"])
    op.create_check_constraint(
        "ck_products_cost_non_negative", "products", "cost_price IS NULL OR cost_price >= 0"
    )

    # ---------- Schema: orders (monetário -> Numeric) ----------
    for col in ("subtotal", "discount", "shipping", "total"):
        op.alter_column("orders", col, type_=sa.Numeric(12, 2),
                        existing_type=sa.Float(), existing_nullable=True,
                        postgresql_using=f"{col}::numeric(12,2)")

    # ---------- Schema: coupons (monetário -> Numeric) ----------
    op.alter_column("coupons", "value", type_=sa.Numeric(12, 2),
                    existing_type=sa.Float(), postgresql_using="value::numeric(12,2)")
    op.alter_column("coupons", "min_order", type_=sa.Numeric(12, 2),
                    existing_type=sa.Float(), existing_nullable=True,
                    postgresql_using="min_order::numeric(12,2)")

    # ---------- Novas tabelas ----------
    op.create_table(
        "product_images",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False, server_default="url"),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.String(), nullable=True),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])

    op.create_table(
        "product_cost_history",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("old_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("new_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("changed_at", sa.String(), nullable=True),
    )
    op.create_index("ix_product_cost_history_product_id", "product_cost_history", ["product_id"])

    # ---------- Migração de dados ----------
    conn = op.get_bind()
    now = _now()

    # Grupos distintos (categorias + produtos)
    cat_groups = [r[0] for r in conn.execute(text('SELECT DISTINCT "group" FROM categories')).fetchall() if r[0]]
    prod_groups = [r[0] for r in conn.execute(text('SELECT DISTINCT "group" FROM products')).fetchall() if r[0]]
    all_groups = list(dict.fromkeys([*GROUP_ORDER, *cat_groups, *prod_groups]))
    all_groups = [g for g in all_groups if g]

    parent_id_by_group = {}
    order = 0
    for g in all_groups:
        existing = conn.execute(text("SELECT id FROM categories WHERE slug = :s"), {"s": g}).fetchone()
        if existing:
            parent_id_by_group[g] = existing[0]
        else:
            new_id = str(uuid.uuid4())
            conn.execute(
                text(
                    'INSERT INTO categories (id, name, slug, "group", parent_id, is_active, sort_order, image, description, created_at, updated_at) '
                    "VALUES (:id, :name, :slug, :grp, NULL, true, :so, '', :desc, :now, :now)"
                ),
                {
                    "id": new_id, "name": GROUP_LABELS.get(g, g.title()), "slug": g, "grp": g,
                    "so": order, "desc": f"Categoria {GROUP_LABELS.get(g, g.title())}.", "now": now,
                },
            )
            parent_id_by_group[g] = new_id
        order += 1

    # Categorias atuais (slug != group) viram subcategorias do pai correspondente.
    for g, pid in parent_id_by_group.items():
        conn.execute(
            text('UPDATE categories SET parent_id = :pid, updated_at = :now '
                 'WHERE "group" = :g AND slug <> :g AND parent_id IS NULL'),
            {"pid": pid, "g": g, "now": now},
        )

    # Vincula produtos às categorias principal/subcategoria.
    products = conn.execute(text('SELECT id, category, "group" FROM products')).fetchall()
    for pid, cat_slug, grp in products:
        main_id, sub_id = None, None
        if cat_slug:
            row = conn.execute(text("SELECT id, parent_id FROM categories WHERE slug = :s"), {"s": cat_slug}).fetchone()
            if row:
                if row[1]:  # tem pai => é subcategoria
                    sub_id = row[0]
                    main_id = row[1]
                else:       # é categoria principal
                    main_id = row[0]
        if main_id is None and grp:
            main_id = parent_id_by_group.get(grp)
        conn.execute(
            text("UPDATE products SET main_category_id = :m, subcategory_id = :s WHERE id = :pid"),
            {"m": main_id, "s": sub_id, "pid": pid},
        )

    # Popula product_images a partir do array images existente.
    rows = conn.execute(text("SELECT id, images FROM products")).fetchall()
    for pid, images in rows:
        if not images:
            continue
        for idx, url in enumerate(images):
            if not url:
                continue
            conn.execute(
                text(
                    "INSERT INTO product_images (id, product_id, source_type, url, sort_order, is_primary, created_at) "
                    "VALUES (:id, :pid, 'url', :url, :so, :prim, :now)"
                ),
                {"id": str(uuid.uuid4()), "pid": pid, "url": url, "so": idx, "prim": (idx == 0), "now": now},
            )


def downgrade() -> None:
    op.drop_index("ix_product_cost_history_product_id", table_name="product_cost_history")
    op.drop_table("product_cost_history")
    op.drop_index("ix_product_images_product_id", table_name="product_images")
    op.drop_table("product_images")

    op.alter_column("coupons", "min_order", type_=sa.Float(), existing_type=sa.Numeric(12, 2), existing_nullable=True)
    op.alter_column("coupons", "value", type_=sa.Float(), existing_type=sa.Numeric(12, 2))

    for col in ("subtotal", "discount", "shipping", "total"):
        op.alter_column("orders", col, type_=sa.Float(), existing_type=sa.Numeric(12, 2), existing_nullable=True)

    op.drop_constraint("ck_products_cost_non_negative", "products", type_="check")
    op.drop_index("ix_products_subcategory_id", table_name="products")
    op.drop_index("ix_products_main_category_id", table_name="products")
    op.drop_column("products", "subcategory_id")
    op.drop_column("products", "main_category_id")
    op.drop_column("products", "cost_price")
    op.alter_column("products", "rating", type_=sa.Float(), existing_type=sa.Numeric(3, 2))
    op.alter_column("products", "compare_at_price", type_=sa.Float(), existing_type=sa.Numeric(12, 2), existing_nullable=True)
    op.alter_column("products", "price", type_=sa.Float(), existing_type=sa.Numeric(12, 2))

    op.drop_constraint("fk_categories_parent", "categories", type_="foreignkey")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_column("categories", "updated_at")
    op.drop_column("categories", "created_at")
    op.drop_column("categories", "sort_order")
    op.drop_column("categories", "is_active")
    op.drop_column("categories", "parent_id")
