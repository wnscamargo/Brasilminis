"""Entrypoint mantido para o supervisor (uvicorn server:app).

Carrega o .env e expõe o app FastAPI definido em app.main.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from app.main import app  # noqa: E402

__all__ = ["app"]
