import re
import unicodedata

from sqlalchemy import inspect as sa_inspect


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text or "item"


def to_dict(obj, exclude: tuple = ()) -> dict | None:
    """Serializa uma instância ORM em dict com apenas as colunas mapeadas."""
    if obj is None:
        return None
    data = {c.key: getattr(obj, c.key) for c in sa_inspect(obj).mapper.column_attrs}
    for e in exclude:
        data.pop(e, None)
    return data
