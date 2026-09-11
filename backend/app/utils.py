import re
import unicodedata
from decimal import Decimal

from sqlalchemy import inspect as sa_inspect


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text or "item"


def _coerce(value):
    # Decimal não é serializável em JSON; converte para float na fronteira da API.
    if isinstance(value, Decimal):
        return float(value)
    return value


def to_dict(obj, exclude: tuple = ()) -> dict | None:
    """Serializa uma instância ORM em dict com apenas as colunas mapeadas."""
    if obj is None:
        return None
    data = {c.key: _coerce(getattr(obj, c.key)) for c in sa_inspect(obj).mapper.column_attrs}
    for e in exclude:
        data.pop(e, None)
    return data
