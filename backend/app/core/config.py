import os


class Settings:
    """Configuração central lida exclusivamente de variáveis de ambiente (.env)."""

    DATABASE_URL: str = os.environ["DATABASE_URL"]
    JWT_SECRET: str = os.environ["JWT_SECRET"]

    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
    ]

    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@brasilminis.com")
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "admin123")

    # Cria as tabelas no startup (conveniência para preview/dev). Em produção (VPS)
    # deixe "false" e use Alembic (`alembic upgrade head`).
    AUTO_CREATE_TABLES: bool = os.environ.get("AUTO_CREATE_TABLES", "false").lower() == "true"

    FREE_SHIPPING_THRESHOLD: float = float(os.environ.get("FREE_SHIPPING_THRESHOLD", "300"))
    STANDARD_SHIPPING: float = float(os.environ.get("STANDARD_SHIPPING", "29.90"))


settings = Settings()
