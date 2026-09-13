"""Métricas financeiras (Dashboard admin). Tudo calculado a partir do PostgreSQL.

CMV usa o custo CONGELADO no item do pedido. Itens sem custo cadastrado no momento
da venda NÃO entram no CMV nem no lucro (são sinalizados separadamente).
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models import Category, Order, Product

CENTS = Decimal("0.01")
Z = Decimal("0.00")


def _money(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(CENTS, rounding=ROUND_HALF_UP)


def _f(d: Decimal) -> float:
    return float(_money(d))


def _parse_date(iso: str):
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return datetime.fromisoformat(iso[:10]).date()
        except Exception:
            return None


def resolve_period(period: str, start: str | None, end: str | None):
    today = datetime.now(timezone.utc).date()
    if period == "today":
        return today, today
    if period == "7d":
        return today - timedelta(days=6), today
    if period == "30d":
        return today - timedelta(days=29), today
    if period == "this_month":
        return today.replace(day=1), today
    if period == "last_month":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        return last_prev.replace(day=1), last_prev
    if period == "custom":
        s = _parse_date(start) or (today - timedelta(days=29))
        e = _parse_date(end) or today
        return s, e
    # default: 30 dias
    return today - timedelta(days=29), today


def compute(db: Session, period: str = "30d", start: str | None = None, end: str | None = None, baseline: str | None = None) -> dict:
    d_start, d_end = resolve_period(period, start, end)

    # Marco de zeragem: aplica-se aos períodos padrão (cards do Dashboard).
    # Períodos "custom" preservam acesso a relatórios históricos anteriores ao marco.
    apply_baseline = bool(baseline) and period != "custom"

    orders = db.query(Order).all()
    in_range = []
    for o in orders:
        if apply_baseline and (o.created_at or "") < baseline:
            continue
        od = _parse_date(o.created_at)
        if od is not None and d_start <= od <= d_end:
            in_range.append(o)

    products = {p.id: p for p in db.query(Product).all()}
    categories = {c.id: c for c in db.query(Category).all()}
    cat_by_slug = {c.slug: c for c in categories.values()}

    revenue_gross = Z
    discounts = Z
    shipping_charged = Z
    total_sum = Z
    cogs = Z
    product_gross_profit = Z            # lucro dos produtos (após desconto atribuível) - CMV
    revenue_with_cost_net = Z           # receita líq. só de itens com custo (base da margem)
    items_without_cost_qty = 0
    orders_without_cost = set()
    products_sold = 0

    by_product: dict = {}   # id -> {name, revenue, profit, qty, has_cost}
    by_main: dict = {}      # cat_id -> revenue
    by_sub: dict = {}       # cat_id -> revenue
    series: dict = {}       # date -> {revenue, cogs, profit}

    for o in in_range:
        o_discount = _money(o.discount)
        o_shipping = _money(o.shipping)
        o_total = _money(o.total)
        items = o.items or []

        order_gross = Z
        for it in items:
            qty = int(it.get("quantity", 0) or 0)
            line_rev = _money(it.get("line_revenue", it.get("line_total", (it.get("price", 0) or 0) * qty)))
            order_gross += line_rev

        revenue_gross += order_gross
        discounts += o_discount
        shipping_charged += o_shipping
        total_sum += o_total

        day = (o.created_at or "")[:10]
        s = series.setdefault(day, {"date": day, "revenue": Z, "cogs": Z, "profit": Z})
        s["revenue"] += order_gross

        for it in items:
            qty = int(it.get("quantity", 0) or 0)
            products_sold += qty
            line_rev = _money(it.get("line_revenue", it.get("line_total", (it.get("price", 0) or 0) * qty)))
            has_cost = it.get("has_cost", it.get("unit_cost_snapshot") is not None)

            # Desconto atribuível ao item (proporcional à receita da linha no pedido)
            alloc_discount = Z
            if order_gross > 0 and o_discount > 0:
                alloc_discount = _money(o_discount * (line_rev / order_gross))
            net_line_rev = _money(line_rev - alloc_discount)

            pid = it.get("product_id")
            prod = products.get(pid)
            name = it.get("name") or (prod.name if prod else "Produto removido")
            entry = by_product.setdefault(pid or name, {
                "product_id": pid, "name": name, "revenue": Z, "profit": Z, "qty": 0, "has_cost": True,
            })
            entry["revenue"] += net_line_rev
            entry["qty"] += qty

            if has_cost and it.get("line_cogs") is not None:
                line_cogs = _money(it.get("line_cogs"))
                line_profit = _money(net_line_rev - line_cogs)
                cogs += line_cogs
                product_gross_profit += line_profit
                revenue_with_cost_net += net_line_rev
                entry["profit"] += line_profit
                s["cogs"] += line_cogs
                s["profit"] += line_profit
            else:
                items_without_cost_qty += qty
                orders_without_cost.add(o.id)
                entry["has_cost"] = False

            # Rankings por categoria (usa categoria ATUAL do produto)
            if prod:
                main_id = prod.main_category_id
                sub_id = prod.subcategory_id
                if not main_id and prod.group and prod.group in cat_by_slug:
                    main_id = cat_by_slug[prod.group].id
                if not sub_id and prod.category and prod.category in cat_by_slug:
                    sub_id = cat_by_slug[prod.category].id
                if main_id:
                    by_main[main_id] = by_main.get(main_id, Z) + net_line_rev
                if sub_id:
                    by_sub[sub_id] = by_sub.get(sub_id, Z) + net_line_rev

    orders_count = len(in_range)
    net_revenue = _money(revenue_gross - discounts + shipping_charged)
    gross_margin_pct = (
        float((product_gross_profit / revenue_with_cost_net * 100).quantize(CENTS))
        if revenue_with_cost_net > 0 else 0.0
    )
    avg_ticket = _money(total_sum / orders_count) if orders_count else Z

    def _rank(entries, key, limit=5, reverse=True):
        out = []
        for e in sorted(entries, key=key, reverse=reverse)[:limit]:
            out.append(e)
        return out

    top_products_revenue = [
        {"product_id": e["product_id"], "name": e["name"], "value": _f(e["revenue"]), "qty": e["qty"]}
        for e in _rank(list(by_product.values()), lambda x: x["revenue"])
    ]
    top_products_profit = [
        {"product_id": e["product_id"], "name": e["name"], "value": _f(e["profit"]), "qty": e["qty"]}
        for e in _rank([e for e in by_product.values() if e["has_cost"]], lambda x: x["profit"])
    ]
    best_sellers = [
        {"product_id": e["product_id"], "name": e["name"], "value": e["qty"]}
        for e in _rank(list(by_product.values()), lambda x: x["qty"])
    ]

    def _cat_rank(bucket):
        rows = []
        for cid, val in bucket.items():
            cat = categories.get(cid)
            rows.append({"id": cid, "name": cat.name if cat else "—", "value": _f(val)})
        return sorted(rows, key=lambda x: x["value"], reverse=True)[:5]

    top_categories_revenue = _cat_rank(by_main)
    top_subcategories_revenue = _cat_rank(by_sub)

    # Produtos com menor margem (catálogo atual, apenas com custo informado e ativos)
    low_margin = []
    for p in products.values():
        if p.cost_price is not None and p.price and float(p.price) > 0 and p.is_active:
            price = _money(p.price)
            cost = _money(p.cost_price)
            margin = float(((price - cost) / price * 100).quantize(CENTS))
            low_margin.append({
                "product_id": p.id, "name": p.name,
                "price": _f(price), "cost": _f(cost), "margin_pct": margin,
            })
    low_margin = sorted(low_margin, key=lambda x: x["margin_pct"])[:5]

    products_without_cost_catalog = db.query(Product).filter(
        Product.cost_price.is_(None), Product.is_active.is_(True)
    ).count()

    series_list = sorted(
        [{"date": v["date"], "revenue": _f(v["revenue"]), "cogs": _f(v["cogs"]), "profit": _f(v["profit"])}
         for v in series.values()],
        key=lambda x: x["date"],
    )

    return {
        "period": {"start": d_start.isoformat(), "end": d_end.isoformat(), "key": period},
        "baseline": baseline if apply_baseline else None,
        "revenue_gross": _f(revenue_gross),
        "discounts": _f(discounts),
        "shipping_charged": _f(shipping_charged),
        "net_revenue": _f(net_revenue),
        "cogs": _f(cogs),
        "gross_profit": _f(product_gross_profit),
        "gross_margin_pct": gross_margin_pct,
        "avg_ticket": _f(avg_ticket),
        "orders_count": orders_count,
        "products_sold": products_sold,
        # Resultado separado (produtos x logística)
        "product_result": _f(product_gross_profit),
        "shipping_revenue": _f(shipping_charged),
        # Transparência sobre custo ausente
        "items_without_cost_qty": items_without_cost_qty,
        "orders_without_cost_count": len(orders_without_cost),
        "products_without_cost_catalog": products_without_cost_catalog,
        # Rankings
        "top_products_revenue": top_products_revenue,
        "top_products_profit": top_products_profit,
        "top_categories_revenue": top_categories_revenue,
        "top_subcategories_revenue": top_subcategories_revenue,
        "low_margin_products": low_margin,
        "best_sellers": best_sellers,
        # Série temporal
        "series": series_list,
    }
