import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models import Banner, Brand, Category, Coupon, Product, User
from app.utils import slugify

IMG = {
    "hero": "https://images.unsplash.com/photo-1637494873826-795116ba38cc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600",
    "diecast": [
        "https://images.unsplash.com/photo-1648711727240-7ee250483923?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1642374386978-9d5befc7af96?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1730291559818-a31641df6859?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1642374452721-19886859ef79?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1780577458908-aa868402b3b6?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1752900135471-956e6c4685af?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1594051673969-172a6f721d3c?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
    ],
    "model": [
        "https://images.unsplash.com/photo-1764308060405-5fd82b66ad11?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1766389647695-bed08ae55f14?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1774682879572-96ec0155fcde?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1519440862171-af26cf8c2a85?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
    ],
    "apparel": [
        "https://images.unsplash.com/photo-1616030257764-0fe6a2f05138?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1601063476271-a159c71ab0b3?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1601754664414-aa3e4f42e6d4?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1517942420142-6a296f9ee4b1?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
    ],
    "accessory": [
        "https://images.unsplash.com/photo-1783253188513-60ccd634a6f6?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1739102174050-85ffaadab43f?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
        "https://images.unsplash.com/photo-1629155362659-c2cf95a01e45?crop=entropy&cs=srgb&fm=jpg&q=85&w=900",
    ],
}

CATEGORIES = [
    ("Diecast 1:64", "miniaturas", "Escala 1:64, o coração do colecionismo automotivo."),
    ("Diecast 1:18", "miniaturas", "Modelos premium em escala 1:18 com detalhes de fábrica."),
    ("JDM Legends", "miniaturas", "Ícones japoneses eternizados em miniatura."),
    ("Supercarros", "miniaturas", "Hipercarros e supercarros dos seus sonhos."),
    ("Treasure Hunt", "colecionaveis", "As caças ao tesouro mais desejadas."),
    ("Super Treasure Hunt", "colecionaveis", "O topo da raridade Hot Wheels."),
    ("Premium", "colecionaveis", "Séries premium com rodas de borracha real."),
    ("Edição Limitada", "colecionaveis", "Tiragens exclusivas e numeradas."),
    ("Dioramas", "colecionaveis", "Cenários realistas para expor sua coleção."),
    ("Garagens", "colecionaveis", "Garagens temáticas em miniatura."),
    ("Displays", "acessorios", "Suportes e displays para exposição."),
    ("Vitrines", "acessorios", "Vitrines acrílicas com proteção UV."),
    ("Cases Acrílicos", "acessorios", "Cases individuais de proteção."),
    ("Iluminação LED", "acessorios", "Kits de LED para valorizar a coleção."),
    ("Kits de Limpeza", "acessorios", "Cuidado e manutenção das miniaturas."),
    ("Bonés", "vestuario", "Bonés automotivos premium."),
    ("Camisetas", "vestuario", "Camisetas com estampas exclusivas."),
    ("Moletons", "vestuario", "Moletons confortáveis para colecionadores."),
    ("Jaquetas", "vestuario", "Jaquetas racing de alto padrão."),
    ("Mochilas", "vestuario", "Mochilas resistentes com identidade Brasil Minis."),
    ("Gift Card", "presentes", "Presenteie quem ama automóveis."),
    ("Mystery Box", "presentes", "A emoção do desconhecido em cada caixa."),
    ("Combos", "presentes", "Combos com o melhor custo-benefício."),
    ("Kits", "presentes", "Kits temáticos montados a dedo."),
]

BRANDS = [
    "Hot Wheels", "Matchbox", "Mini GT", "Inno64", "Kaido House",
    "Tomica", "Greenlight", "Majorette", "Tarmac Works", "M2 Machines",
]


def _product(name, price, category, group, brand, imgs, stock, badges, compare=None, featured=False, desc="", specs=None):
    return Product(
        id=str(uuid.uuid4()),
        name=name,
        slug=slugify(name),
        description=desc or f"{name} — item premium da curadoria Brasil Minis, ideal para colecionadores exigentes.",
        price=price,
        compare_at_price=compare,
        category=category,
        group=group,
        brand=brand,
        images=imgs,
        stock=stock,
        badges=badges,
        specs=specs or {},
        rating=0,
        reviews_count=0,
        featured=featured,
        is_active=True,
        created_at=(datetime.now(timezone.utc) - timedelta(days=len(name) % 20)).isoformat(),
    )


def _build_products():
    d = IMG["diecast"]
    m = IMG["model"]
    a = IMG["apparel"]
    ac = IMG["accessory"]
    p = [
        _product("Porsche 911 GT3 RS 1:64", 89.90, "diecast-1-64", "miniaturas", "mini-gt", [d[4], d[5]], 24,
                 ["LANÇAMENTO"], featured=True, specs={"Escala": "1:64", "Material": "Zamac", "Rodas": "Borracha real"}),
        _product("Nissan Skyline GT-R R34 1:64", 74.90, "jdm-legends", "miniaturas", "kaido-house", [d[3], d[2]], 18,
                 ["TREASURE HUNT"], featured=True, specs={"Escala": "1:64", "Série": "Kaido House x Mini GT"}),
        _product("Ford Mustang Boss 302 1:64", 59.90, "diecast-1-64", "miniaturas", "greenlight", [d[0]], 40,
                 ["NOVO"], desc="Clássico muscle car americano em acabamento premium.", specs={"Escala": "1:64"}),
        _product("Toyota Supra MK4 JDM 1:64", 99.90, "jdm-legends", "miniaturas", "inno64", [d[1]], 12,
                 ["SUPER TH"], compare=129.90, featured=True, specs={"Escala": "1:64", "Edição": "Limitada"}),
        _product("Lamborghini Aventador 1:18", 349.90, "diecast-1-18", "miniaturas", "tarmac-works", [m[0], m[2]], 8,
                 ["PREMIUM", "FRETE GRÁTIS"], featured=True, specs={"Escala": "1:18", "Portas": "Abrem"}),
        _product("McLaren 720S Amarelo 1:18", 379.90, "supercarros", "miniaturas", "tarmac-works", [m[3], m[1]], 6,
                 ["EDIÇÃO LIMITADA"], compare=449.90, specs={"Escala": "1:18"}),
        _product("BMW M3 E30 Preto 1:64", 69.90, "diecast-1-64", "miniaturas", "tomica", [d[6]], 30,
                 ["NOVO"], specs={"Escala": "1:64"}),
        _product("Honda Civic Type R 1:64", 64.90, "jdm-legends", "miniaturas", "majorette", [d[2]], 22,
                 ["PROMOÇÃO"], compare=84.90, specs={"Escala": "1:64"}),
        _product("Chevrolet Camaro SS 1:64", 54.90, "diecast-1-64", "miniaturas", "m2-machines", [d[0], d[3]], 35,
                 [], specs={"Escala": "1:64"}),
        _product("VW Fusca Racing 1:64", 49.90, "diecast-1-64", "miniaturas", "hot-wheels", [d[1]], 50,
                 ["NOVO"], featured=True, specs={"Escala": "1:64"}),
        _product("Set Treasure Hunt 2025 (5 peças)", 199.90, "treasure-hunt", "colecionaveis", "hot-wheels", [d[0], d[1]], 10,
                 ["TREASURE HUNT", "FRETE GRÁTIS"], featured=True),
        _product("Super TH Datsun 240Z", 159.90, "super-th", "colecionaveis", "hot-wheels", [d[3]], 5,
                 ["SUPER TH", "PRÉ-VENDA"], compare=189.90),
        _product("Diorama Posto Retrô 1:64", 129.90, "dioramas", "colecionaveis", "greenlight", [ac[0]], 14,
                 ["LANÇAMENTO"], desc="Cenário detalhado de posto de gasolina retrô."),
        _product("Garagem 3 Andares 1:64", 179.90, "garagens", "colecionaveis", "greenlight", [ac[1]], 9,
                 ["NOVO"]),
        _product("Display Acrílico 12 Nichos", 149.90, "displays", "acessorios", "", [ac[0], ac[2]], 20,
                 ["FRETE GRÁTIS"], featured=True, desc="Organize e exponha sua coleção com elegância."),
        _product("Vitrine LED 1:18", 259.90, "vitrines", "acessorios", "", [ac[1]], 7,
                 ["PREMIUM"], compare=299.90),
        _product("Case Acrílico Individual (10un)", 79.90, "cases-acrilicos", "acessorios", "", [ac[2]], 60,
                 []),
        _product("Kit Fita LED USB Colecionador", 89.90, "led", "acessorios", "", [ac[0]], 25,
                 ["NOVO"]),
        _product("Kit de Limpeza Premium", 44.90, "kits-limpeza", "acessorios", "", [ac[2]], 40,
                 ["PROMOÇÃO"], compare=59.90),
        _product("Boné Brasil Minis Racing", 89.90, "bones", "vestuario", "", [a[0]], 30,
                 ["NOVO"], featured=True),
        _product("Camiseta JDM Legends", 79.90, "camisetas", "vestuario", "", [a[2]], 45,
                 ["LANÇAMENTO"]),
        _product("Moletom Premium Carbon", 189.90, "moletons", "vestuario", "", [a[1], a[3]], 20,
                 ["FRETE GRÁTIS"], featured=True),
        _product("Jaqueta Racing Team", 349.90, "jaquetas", "vestuario", "", [a[3]], 8,
                 ["PREMIUM"], compare=399.90),
        _product("Mochila Colecionador", 219.90, "mochilas", "vestuario", "", [a[1]], 15,
                 []),
        _product("Gift Card R$ 150", 150.00, "gift-card", "presentes", "", [IMG["hero"]], 999,
                 ["NOVO"]),
        _product("Mystery Box Colecionador", 149.90, "mystery-box", "presentes", "", [d[0], d[1]], 30,
                 ["PROMOÇÃO", "FRETE GRÁTIS"], compare=199.90, featured=True,
                 desc="5 miniaturas surpresa selecionadas pela nossa curadoria."),
        _product("Combo Iniciante (3 minis + display)", 219.90, "combos", "presentes", "", [ac[0], d[2]], 18,
                 ["PROMOÇÃO"], compare=269.90),
        _product("Kit Presente JDM", 189.90, "kits", "presentes", "", [d[1], a[2]], 22,
                 ["NOVO"]),
    ]
    return p


COUPONS = [
    {"code": "BRASIL10", "type": "percent", "value": 10, "min_order": 100, "active": True,
     "description": "10% de desconto acima de R$100"},
    {"code": "MINIS20", "type": "percent", "value": 20, "min_order": 300, "active": True,
     "description": "20% de desconto acima de R$300"},
    {"code": "FRETEGRATIS", "type": "fixed", "value": 29.9, "min_order": 0, "active": True,
     "description": "Frete grátis"},
]


def seed_admin(db: Session):
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if admin is None:
        db.add(User(
            id=str(uuid.uuid4()),
            name="Administrador",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            phone="",
            newsletter=False,
            addresses=[],
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
        db.commit()
    elif not verify_password(settings.ADMIN_PASSWORD, admin.password_hash):
        admin.password_hash = hash_password(settings.ADMIN_PASSWORD)
        db.commit()


def seed_data(db: Session):
    if (db.query(func.count(Category.id)).scalar() or 0) == 0:
        db.add_all([
            Category(id=str(uuid.uuid4()), name=name, slug=slugify(name), group=group, description=desc, image="")
            for name, group, desc in CATEGORIES
        ])
        db.commit()

    if (db.query(func.count(Brand.id)).scalar() or 0) == 0:
        db.add_all([
            Brand(id=str(uuid.uuid4()), name=b, slug=slugify(b), logo="", description=f"Produtos oficiais {b}.")
            for b in BRANDS
        ])
        db.commit()

    if (db.query(func.count(Product.id)).scalar() or 0) == 0:
        db.add_all(_build_products())
        db.commit()

    if (db.query(func.count(Banner.id)).scalar() or 0) == 0:
        db.add(Banner(
            id=str(uuid.uuid4()),
            title="Sua paixão em miniatura.",
            subtitle="As melhores marcas e edições exclusivas estão aqui.",
            image=IMG["hero"],
            cta_text="Comprar Agora",
            cta_link="/produtos",
            position=0,
            active=True,
        ))
        db.commit()

    if (db.query(func.count(Coupon.code)).scalar() or 0) == 0:
        db.add_all([Coupon(**c) for c in COUPONS])
        db.commit()
