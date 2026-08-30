from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
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
    group: str  # miniaturas | colecionaveis | acessorios | vestuario | presentes
    image: Optional[str] = ""
    description: Optional[str] = ""


class BrandInput(BaseModel):
    name: str
    slug: Optional[str] = None
    logo: Optional[str] = ""
    description: Optional[str] = ""


class ProductInput(BaseModel):
    name: str
    slug: Optional[str] = None
    description: str = ""
    price: float
    compare_at_price: Optional[float] = None
    category: str  # category slug
    group: Optional[str] = ""
    brand: Optional[str] = ""  # brand slug
    images: List[str] = []
    stock: int = 0
    badges: List[str] = []
    specs: dict = {}
    featured: bool = False
    is_active: bool = True


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


class CouponValidateInput(BaseModel):
    code: str


class OrderStatusInput(BaseModel):
    status: str


# ---------- Banners ----------
class BannerInput(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    image: str
    cta_text: Optional[str] = ""
    cta_link: Optional[str] = ""
    position: int = 0
    active: bool = True
