import os
from pathlib import Path as _Path


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

    # ----- Melhor Envio (FASE SANDBOX; produção não ativada) -----
    MELHOR_ENVIO_ENV: str = os.environ.get("MELHOR_ENVIO_ENV", "sandbox")
    MELHOR_ENVIO_CLIENT_ID: str = os.environ.get("MELHOR_ENVIO_CLIENT_ID", "")
    MELHOR_ENVIO_CLIENT_SECRET: str = os.environ.get("MELHOR_ENVIO_CLIENT_SECRET", "")
    MELHOR_ENVIO_REDIRECT_URI: str = os.environ.get("MELHOR_ENVIO_REDIRECT_URI", "")
    MELHOR_ENVIO_USER_AGENT_EMAIL: str = os.environ.get("MELHOR_ENVIO_USER_AGENT_EMAIL", "contato@brasilminis.com")
    MELHOR_ENVIO_TOKEN_ENCRYPTION_KEY: str = os.environ.get("MELHOR_ENVIO_TOKEN_ENCRYPTION_KEY", "")
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "")

    @property
    def MELHOR_ENVIO_BASE_URL(self) -> str:
        return (
            "https://sandbox.melhorenvio.com.br"
            if (self.MELHOR_ENVIO_ENV or "sandbox").lower() == "sandbox"
            else "https://melhorenvio.com.br"
        )

    @property
    def MELHOR_ENVIO_USER_AGENT(self) -> str:
        return f"Brasil Minis ({self.MELHOR_ENVIO_USER_AGENT_EMAIL})"

    @property
    def MELHOR_ENVIO_CONFIGURED(self) -> bool:
        return bool(self.MELHOR_ENVIO_CLIENT_ID and self.MELHOR_ENVIO_CLIENT_SECRET and self.MELHOR_ENVIO_REDIRECT_URI)

    # Armazenamento persistente de uploads (NUNCA dentro de frontend/build).
    # Preview: backend/uploads (persiste em /app). VPS: /var/www/brasilminis/uploads.
    UPLOADS_DIR: str = os.environ.get(
        "UPLOADS_DIR", str(_Path(__file__).resolve().parents[2] / "uploads")
    )


settings = Settings()
