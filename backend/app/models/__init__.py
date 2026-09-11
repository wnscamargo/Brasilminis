import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="customer")
    phone = Column(String, default="")
    newsletter = Column(Boolean, default=False)
    addresses = Column(JSONB, default=list)
    created_at = Column(String, default=_now_iso)


class Category(Base):
    """Categoria hierárquica. parent_id=None => categoria principal; caso contrário, subcategoria."""
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    group = Column(String, nullable=False, index=True)  # compat: grupo de topo (= slug da principal)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    image = Column(String, default="")
    description = Column(Text, default="")
    created_at = Column(String, default=_now_iso)
    updated_at = Column(String, nullable=True)


class Brand(Base):
    __tablename__ = "brands"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    logo = Column(String, default="")
    description = Column(Text, default="")


class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    price = Column(Numeric(12, 2), nullable=False)
    compare_at_price = Column(Numeric(12, 2), nullable=True)
    cost_price = Column(Numeric(12, 2), nullable=True)  # None => custo ainda não informado
    category = Column(String, default="", index=True)  # slug da subcategoria (compat)
    group = Column(String, default="", index=True)     # slug da categoria principal (compat)
    main_category_id = Column(String, index=True, nullable=True)
    subcategory_id = Column(String, index=True, nullable=True)
    brand = Column(String, default="", index=True)  # slug da marca
    images = Column(JSONB, default=list)  # cache denormalizado (ordenado) para o storefront
    stock = Column(Integer, default=0)
    # Dados logísticos (Melhor Envio). None => incompleto para cotação.
    weight_kg = Column(Numeric(8, 3), nullable=True)
    width_cm = Column(Numeric(8, 2), nullable=True)
    height_cm = Column(Numeric(8, 2), nullable=True)
    length_cm = Column(Numeric(8, 2), nullable=True)
    sku = Column(String, nullable=True)
    barcode = Column(String, nullable=True)
    badges = Column(JSONB, default=list)
    specs = Column(JSONB, default=dict)
    rating = Column(Numeric(3, 2), default=0)
    reviews_count = Column(Integer, default=0)
    featured = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(String, default=_now_iso, index=True)

    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        CheckConstraint("cost_price IS NULL OR cost_price >= 0", name="ck_products_cost_non_negative"),
    )


class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String, nullable=False, default="url")  # url | upload
    url = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(String, default=_now_iso)


class ProductCostHistory(Base):
    __tablename__ = "product_cost_history"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, index=True, nullable=False)
    old_cost = Column(Numeric(12, 2), nullable=True)
    new_cost = Column(Numeric(12, 2), nullable=True)
    changed_by = Column(String, nullable=True)
    changed_at = Column(String, default=_now_iso)


class Favorite(Base):
    __tablename__ = "favorites"
    user_id = Column(String, primary_key=True)
    product_id = Column(String, primary_key=True)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True, default=_uuid)
    product_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    user_name = Column(String)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(String, default=_now_iso)


class Coupon(Base):
    __tablename__ = "coupons"
    code = Column(String, primary_key=True)
    type = Column(String, nullable=False)  # percent | fixed
    value = Column(Numeric(12, 2), nullable=False)
    min_order = Column(Numeric(12, 2), default=0)
    active = Column(Boolean, default=True)
    description = Column(String, default="")


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=_uuid)
    order_number = Column(String, index=True)
    user_id = Column(String, nullable=False, index=True)
    user_name = Column(String)
    user_email = Column(String)
    items = Column(JSONB, default=list)  # inclui snapshots de custo/preço por linha
    subtotal = Column(Numeric(12, 2))
    discount = Column(Numeric(12, 2), default=0)
    coupon = Column(String, nullable=True)
    shipping = Column(Numeric(12, 2), default=0)
    shipping_method = Column(String)
    # Snapshot do frete congelado no momento do pedido (Melhor Envio)
    shipping_provider = Column(String, nullable=True)
    shipping_service_id = Column(Integer, nullable=True)
    shipping_service_name = Column(String, nullable=True)
    shipping_company_id = Column(Integer, nullable=True)
    shipping_company_name = Column(String, nullable=True)
    shipping_price_customer = Column(Numeric(12, 2), nullable=True)  # cobrado do cliente
    shipping_price_quoted = Column(Numeric(12, 2), nullable=True)    # custo real cotado
    shipping_delivery_min = Column(Integer, nullable=True)
    shipping_delivery_max = Column(Integer, nullable=True)
    shipping_destination_postal_code = Column(String, nullable=True)
    shipping_quote_snapshot = Column(JSONB, nullable=True)
    recipient_snapshot = Column(JSONB, nullable=True)
    total = Column(Numeric(12, 2))
    payment_method = Column(String)
    payment_status = Column(String)
    status = Column(String, index=True)
    address = Column(JSONB, nullable=True)
    created_at = Column(String, default=_now_iso, index=True)


class Banner(Base):
    __tablename__ = "banners"
    id = Column(String, primary_key=True, default=_uuid)
    title = Column(String)
    subtitle = Column(String, default="")
    image = Column(String)
    cta_text = Column(String, default="")
    cta_link = Column(String, default="")
    position = Column(Integer, default=0, index=True)
    active = Column(Boolean, default=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    token = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
    used = Column(Boolean, default=False)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    identifier = Column(String, primary_key=True)
    count = Column(Integer, default=0)
    locked_until = Column(String, nullable=True)


class SiteSettings(Base):
    """Configuração global do site (linha única, id=1). Modo 'em construção'."""
    __tablename__ = "site_settings"
    id = Column(Integer, primary_key=True, default=1)
    maintenance_enabled = Column(Boolean, nullable=False, default=False)
    maintenance_title = Column(String, default="Estamos preparando algo incrível")
    maintenance_subtitle = Column(String, default="")
    maintenance_message = Column(Text, default="")
    launch_date = Column(String, nullable=True)  # ISO 8601
    show_countdown = Column(Boolean, default=False)
    whatsapp_url = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    show_whatsapp = Column(Boolean, default=False)
    show_instagram = Column(Boolean, default=False)
    # Identidade visual GLOBAL (usada pelo site e reutilizada pela manutenção)
    logo_url = Column(String, nullable=True)       # None => usa a logo padrão (fallback)
    logo_width = Column(Integer, default=200)       # largura máx. no desktop (px)
    branding = Column(JSONB, default=dict)          # extensível: favicon, cores, og, etc.
    updated_at = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)


# ================= Melhor Envio (SANDBOX) =================
class MelhorEnvioToken(Base):
    """Token OAuth (linha única, id=1). Tokens armazenados CRIPTOGRAFADOS (Fernet)."""
    __tablename__ = "melhor_envio_tokens"
    id = Column(Integer, primary_key=True, default=1)
    access_token_enc = Column(Text, nullable=True)
    refresh_token_enc = Column(Text, nullable=True)
    expires_at = Column(String, nullable=True)  # ISO 8601 (UTC)
    scope = Column(String, nullable=True)
    token_type = Column(String, nullable=True)
    account_email = Column(String, nullable=True)  # e-mail da conta ME conectada
    environment = Column(String, default="sandbox")
    pending_state = Column(String, nullable=True)  # CSRF state do OAuth em andamento
    last_error = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)


class MelhorEnvioSender(Base):
    """Dados do remetente (linha única, id=1). Configurável pelo admin."""
    __tablename__ = "melhor_envio_sender"
    id = Column(Integer, primary_key=True, default=1)
    name = Column(String, default="")
    company = Column(String, default="")
    email = Column(String, default="")
    phone = Column(String, default="")
    document = Column(String, default="")        # CPF/CNPJ
    state_register = Column(String, default="")  # IE
    postal_code = Column(String, default="")
    address = Column(String, default="")
    number = Column(String, default="")
    complement = Column(String, default="")
    district = Column(String, default="")
    city = Column(String, default="")
    state_abbr = Column(String, default="")
    updated_at = Column(String, nullable=True)


class MelhorEnvioShipment(Base):
    """Ciclo de vida do envio no Melhor Envio (1:1 com o pedido)."""
    __tablename__ = "melhor_envio_shipments"
    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    cart_order_id = Column(String, nullable=True, index=True)  # UUID do frete no carrinho ME
    protocol = Column(String, nullable=True)
    # Estado interno: pending | prepared | in_cart | purchased | generated | posted | delivered | cancelled | error
    internal_status = Column(String, default="pending", index=True)
    external_status = Column(String, nullable=True)  # status original do ME (não perder)
    tracking_code = Column(String, nullable=True)
    label_url = Column(String, nullable=True)
    price = Column(Numeric(12, 2), nullable=True)  # custo real da etiqueta (negócio)
    service_id = Column(Integer, nullable=True)
    service_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    inserted_at = Column(String, nullable=True)
    purchased_at = Column(String, nullable=True)
    generated_at = Column(String, nullable=True)
    posted_at = Column(String, nullable=True)
    delivered_at = Column(String, nullable=True)
    last_tracking_update_at = Column(String, nullable=True)
    timeline = Column(JSONB, default=list)
    raw = Column(JSONB, nullable=True)
    last_error = Column(String, nullable=True)
    created_at = Column(String, default=_now_iso)
    updated_at = Column(String, nullable=True)


class ShippingQuote(Base):
    """Cotação com validade (expiração). Congela peso/dimensões/opções no servidor."""
    __tablename__ = "shipping_quotes"
    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, nullable=True, index=True)
    destination_postal_code = Column(String, nullable=False)
    items = Column(JSONB, default=list)     # [{product_id, quantity}]
    volumes = Column(JSONB, default=list)   # payload de volumes enviado ao ME
    results = Column(JSONB, default=list)   # opções normalizadas
    created_at = Column(String, default=_now_iso)
    expires_at = Column(String, nullable=False)


class MelhorEnvioWebhookEvent(Base):
    """Deduplicação/idempotência de webhooks."""
    __tablename__ = "melhor_envio_webhook_events"
    id = Column(String, primary_key=True)  # hash do corpo (idempotência)
    event = Column(String, nullable=True)
    order_ref = Column(String, nullable=True, index=True)
    payload = Column(JSONB, nullable=True)
    received_at = Column(String, default=_now_iso)
