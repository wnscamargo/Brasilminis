from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------- Auth ----------
class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    cpf: str
    newsletter: bool = False


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordInput(BaseModel):
    email: EmailStr


class ResetPasswordInput(BaseModel):
    token: str
    password: str = Field(min_length=6)


# ---------- Account ----------
class ProfileInput(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    newsletter: Optional[bool] = None


class PasswordChangeInput(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class Address(BaseModel):
    id: Optional[str] = None
    label: str
    recipient: str
    street: str
    number: str
    complement: Optional[str] = ""
    district: str
    city: str
    state: str
    zip: str
    is_default: bool = False


# ---------- Catalog ----------
class CategoryInput(BaseModel):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None  # None => categoria principal
    group: Optional[str] = None      # compat (derivado automaticamente)
    is_active: bool = True
    sort_order: int = 0
    image: Optional[str] = ""
    description: Optional[str] = ""


class CategoryReorderInput(BaseModel):
    ids: List[str]  # nova ordem (sort_order = índice)


class BrandInput(BaseModel):
    name: str
    slug: Optional[str] = None
    logo: Optional[str] = ""
    description: Optional[str] = ""


class ProductInput(BaseModel):
    name: str
    slug: Optional[str] = None
    description: str = ""
    price: float = Field(ge=0)
    compare_at_price: Optional[float] = Field(default=None, ge=0)
    cost_price: Optional[float] = Field(default=None, ge=0)  # None => não informado
    category: Optional[str] = ""   # slug da subcategoria (compat)
    group: Optional[str] = ""      # slug da categoria principal (compat)
    main_category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    brand: Optional[str] = ""  # brand slug
    images: List[str] = []
    stock: int = 0
    weight_kg: Optional[float] = Field(default=None, ge=0)
    width_cm: Optional[float] = Field(default=None, ge=0)
    height_cm: Optional[float] = Field(default=None, ge=0)
    length_cm: Optional[float] = Field(default=None, ge=0)
    sku: Optional[str] = None
    barcode: Optional[str] = None
    badges: List[str] = []
    specs: dict = {}
    featured: bool = False
    is_active: bool = True


# ---------- Product images ----------
class ProductImageUrlInput(BaseModel):
    url: str
    is_primary: bool = False

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v):
        v = (v or "").strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v


class ImageReorderInput(BaseModel):
    ids: List[str]


# ---------- Reviews ----------
class ReviewInput(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


# ---------- Orders ----------
class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class CheckoutInput(BaseModel):
    items: List[OrderItemInput]
    shipping_method: str = "standard"
    payment_method: str = "pix"  # pix | card | boleto
    coupon: Optional[str] = None
    address: Optional[Address] = None
    # Melhor Envio: cotação selecionada (congelada no pedido)
    quote_id: Optional[str] = None
    shipping_service_id: Optional[int] = None
    recipient_document: Optional[str] = None
    recipient_phone: Optional[str] = None


# ---------- Melhor Envio ----------
class ShippingQuoteInput(BaseModel):
    postal_code: str
    items: List[OrderItemInput]


class SenderInput(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    document: Optional[str] = None
    state_register: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state_abbr: Optional[str] = None


# ---------- Mercado Pago ----------
class MpSettingsInput(BaseModel):
    environment: str = "test"
    public_key: Optional[str] = None
    access_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_enabled: bool = False


class MpActivateInput(BaseModel):
    confirm: bool = False


# ---------- Melhor Envio: credenciais operacionais (painel) ----------
class MelhorEnvioCredentialsInput(BaseModel):
    environment: str = "sandbox"  # sandbox | production
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None


class PixPaymentInput(BaseModel):
    order_id: str


class CardPaymentInput(BaseModel):
    order_id: str
    token: str
    installments: int = 1
    payment_method_id: str
    issuer_id: Optional[int] = None
    payer_email: Optional[str] = None


class CouponValidateInput(BaseModel):
    code: str


class CouponPreviewInput(BaseModel):
    code: str
    items: List[OrderItemInput]


class CouponInput(BaseModel):
    code: str
    type: str = "percent"  # percent | fixed
    value: float
    min_order: float = 0
    max_discount: Optional[float] = None
    active: bool = True
    description: Optional[str] = ""
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    first_purchase_only: bool = False
    free_shipping: bool = False
    allow_stacking: bool = False
    scope_type: str = "all"  # all | categories | products
    scope_category_ids: List[str] = []
    scope_product_ids: List[str] = []


class CouponGenerateInput(BaseModel):
    prefix: Optional[str] = "BM"
    length: int = 8


class OrderDeleteInput(BaseModel):
    reason: str
    confirm: str  # deve ser exatamente "EXCLUIR"


class OrderStatusInput(BaseModel):
    status: str


# ---------- Exclusão protegida de clientes ----------
class CustomerDeleteInput(BaseModel):
    reason: str
    confirm: str            # deve ser exatamente "EXCLUIR"
    anonymize: bool = False  # LGPD: apaga PII e libera e-mail/CPF para reuso


# ---------- Zeragem administrativa do Dashboard ----------
class DashboardResetInput(BaseModel):
    reason: str
    confirm: str            # deve ser exatamente "ZERAR DASHBOARD"


# ---------- Banners ----------
class BannerInput(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    image: str
    cta_text: Optional[str] = ""
    cta_link: Optional[str] = ""
    position: int = 0
    active: bool = True


# ---------- Site Settings (modo em construção) ----------
class SiteSettingsInput(BaseModel):
    maintenance_enabled: bool = False
    maintenance_title: str = "Estamos preparando algo incrível"
    maintenance_subtitle: Optional[str] = ""
    maintenance_message: Optional[str] = ""
    launch_date: Optional[str] = None
    show_countdown: bool = False
    whatsapp_url: Optional[str] = None
    instagram_url: Optional[str] = None
    show_whatsapp: bool = False
    show_instagram: bool = False

    @field_validator("whatsapp_url", "instagram_url")
    @classmethod
    def _validate_url(cls, v):
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        return v


# ---------- Identidade visual global ----------
class SiteConfigInput(BaseModel):
    logo_width: int = Field(default=200, ge=60, le=500)
    branding: Optional[dict] = None


# ---------- Conteúdo institucional (Sobre, Contato, Trocas, Frete) ----------
class InstitutionalPage(BaseModel):
    title: Optional[str] = ""
    subtitle: Optional[str] = ""
    content: Optional[str] = ""  # Markdown (sanitizado no servidor)
    active: bool = True
    seo_title: Optional[str] = ""
    seo_description: Optional[str] = ""
    # Campos estruturados (usados sobretudo na página Contato)
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    hours: Optional[str] = None
    address: Optional[str] = None
    map_url: Optional[str] = None


class SiteContentInput(BaseModel):
    about: Optional[InstitutionalPage] = None
    contact: Optional[InstitutionalPage] = None
    returns: Optional[InstitutionalPage] = None
    shipping: Optional[InstitutionalPage] = None


# ---------- Redes sociais ----------
class SocialLink(BaseModel):
    url: Optional[str] = ""
    active: bool = False


class SocialLinksInput(BaseModel):
    instagram: Optional[SocialLink] = None
    facebook: Optional[SocialLink] = None
    tiktok: Optional[SocialLink] = None
    youtube: Optional[SocialLink] = None
    whatsapp: Optional[SocialLink] = None
    telegram: Optional[SocialLink] = None
    twitter: Optional[SocialLink] = None
    pinterest: Optional[SocialLink] = None
