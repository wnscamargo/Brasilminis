import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Float,
    Integer,
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
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    group = Column(String, nullable=False, index=True)
    image = Column(String, default="")
    description = Column(Text, default="")


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
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float, nullable=True)
    category = Column(String, default="", index=True)  # slug da categoria
    group = Column(String, default="", index=True)
    brand = Column(String, default="", index=True)  # slug da marca
    images = Column(JSONB, default=list)
    stock = Column(Integer, default=0)
    badges = Column(JSONB, default=list)
    specs = Column(JSONB, default=dict)
    rating = Column(Float, default=0)
    reviews_count = Column(Integer, default=0)
    featured = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(String, default=_now_iso, index=True)

    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
    )


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
    value = Column(Float, nullable=False)
    min_order = Column(Float, default=0)
    active = Column(Boolean, default=True)
    description = Column(String, default="")


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=_uuid)
    order_number = Column(String, index=True)
    user_id = Column(String, nullable=False, index=True)
    user_name = Column(String)
    user_email = Column(String)
    items = Column(JSONB, default=list)
    subtotal = Column(Float)
    discount = Column(Float, default=0)
    coupon = Column(String, nullable=True)
    shipping = Column(Float, default=0)
    shipping_method = Column(String)
    total = Column(Float)
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
