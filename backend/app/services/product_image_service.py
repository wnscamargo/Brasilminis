import io
import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Product, ProductImage
from app.utils import to_dict

ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_BYTES = 8 * 1024 * 1024      # 8 MB
MAX_DIM = 6000                    # px


def _products_dir() -> str:
    from app.core.config import settings
    d = os.path.join(settings.UPLOADS_DIR, "products")
    os.makedirs(d, exist_ok=True)
    return d


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get_product(db: Session, product_id: str) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


def list_images(db: Session, product_id: str) -> list:
    _get_product(db, product_id)
    imgs = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.is_primary.desc(), ProductImage.sort_order.asc())
        .all()
    )
    return [to_dict(i) for i in imgs]


def _ensure_single_primary(db: Session, product_id: str):
    imgs = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.sort_order.asc())
        .all()
    )
    if not imgs:
        return
    primaries = [i for i in imgs if i.is_primary]
    if not primaries:
        imgs[0].is_primary = True
    elif len(primaries) > 1:
        for i in primaries[1:]:
            i.is_primary = False


def sync_product_images(db: Session, product_id: str):
    """Reconstrói o cache denormalizado product.images (principal primeiro)."""
    _ensure_single_primary(db, product_id)
    imgs = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.is_primary.desc(), ProductImage.sort_order.asc())
        .all()
    )
    product = db.get(Product, product_id)
    if product is not None:
        product.images = [i.url for i in imgs]


def add_url_image(db: Session, product_id: str, url: str, is_primary: bool) -> dict:
    _get_product(db, product_id)
    count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    if count == 0:
        is_primary = True
    img = ProductImage(
        id=str(uuid.uuid4()),
        product_id=product_id,
        source_type="url",
        url=url,
        sort_order=count,
        is_primary=is_primary,
        created_at=_now(),
    )
    if is_primary:
        for other in db.query(ProductImage).filter(ProductImage.product_id == product_id).all():
            other.is_primary = False
    db.add(img)
    db.flush()
    sync_product_images(db, product_id)
    db.commit()
    db.refresh(img)
    return to_dict(img)


def upload_image(db: Session, product_id: str, content_type: str, content: bytes) -> dict:
    from PIL import Image

    _get_product(db, product_id)
    ext = ALLOWED.get((content_type or "").lower())
    if not ext:
        raise HTTPException(status_code=400, detail="Formato inválido. Use JPEG, PNG ou WEBP.")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx. 8MB).")
    # Valida MIME real via Pillow (não confia na extensão/cabeçalho enviado).
    try:
        Image.open(io.BytesIO(content)).verify()
        probe = Image.open(io.BytesIO(content))
        real_format = (probe.format or "").lower()
        w, h = probe.size
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem inválida ou corrompida.")
    valid_formats = {"jpeg": "jpg", "png": "png", "webp": "webp"}
    if real_format not in valid_formats:
        raise HTTPException(status_code=400, detail="Conteúdo não é uma imagem JPEG/PNG/WEBP válida.")
    if w > MAX_DIM or h > MAX_DIM or w < 1 or h < 1:
        raise HTTPException(status_code=400, detail="Dimensões da imagem fora do permitido.")

    ext = valid_formats[real_format]
    name = f"prod-{uuid.uuid4().hex}.{ext}"  # nome próprio (UUID), sem path traversal
    with open(os.path.join(_products_dir(), name), "wb") as f:
        f.write(content)

    count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    img = ProductImage(
        id=str(uuid.uuid4()),
        product_id=product_id,
        source_type="upload",
        url=f"/api/uploads/products/{name}",
        sort_order=count,
        is_primary=(count == 0),
        created_at=_now(),
    )
    db.add(img)
    db.flush()
    sync_product_images(db, product_id)
    db.commit()
    db.refresh(img)
    return to_dict(img)


def _remove_file_if_upload(img: ProductImage):
    if img.source_type == "upload" and img.url and img.url.startswith("/api/uploads/products/"):
        name = os.path.basename(img.url)
        path = os.path.join(_products_dir(), name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass


def delete_image(db: Session, product_id: str, image_id: str) -> dict:
    img = db.query(ProductImage).filter(
        ProductImage.id == image_id, ProductImage.product_id == product_id
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    _remove_file_if_upload(img)
    db.delete(img)
    db.flush()
    sync_product_images(db, product_id)
    db.commit()
    return {"message": "Imagem removida"}


def set_primary(db: Session, product_id: str, image_id: str) -> list:
    target = db.query(ProductImage).filter(
        ProductImage.id == image_id, ProductImage.product_id == product_id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    for img in db.query(ProductImage).filter(ProductImage.product_id == product_id).all():
        img.is_primary = img.id == image_id
    db.flush()
    sync_product_images(db, product_id)
    db.commit()
    return list_images(db, product_id)


def reorder_images(db: Session, product_id: str, ids: list) -> list:
    for index, iid in enumerate(ids):
        img = db.query(ProductImage).filter(
            ProductImage.id == iid, ProductImage.product_id == product_id
        ).first()
        if img:
            img.sort_order = index
    db.flush()
    sync_product_images(db, product_id)
    db.commit()
    return list_images(db, product_id)


def seed_images_from_urls(db: Session, product_id: str, urls: list):
    """Cria as linhas product_images a partir de uma lista de URLs (para seed/import)."""
    for index, url in enumerate(urls or []):
        db.add(ProductImage(
            id=str(uuid.uuid4()),
            product_id=product_id,
            source_type="url",
            url=url,
            sort_order=index,
            is_primary=(index == 0),
            created_at=_now(),
        ))
