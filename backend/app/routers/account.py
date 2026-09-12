import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.security import hash_password, verify_password
from app.core.cpf import is_valid_cpf, normalize_cpf
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import Address, PasswordChangeInput, ProfileInput

router = APIRouter(prefix="/api/account", tags=["account"])


def _public(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": user.phone or "",
        "cpf": user.cpf or "",
        "newsletter": bool(user.newsletter),
    }


@router.put("/profile")
def update_profile(payload: ProfileInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    fresh = db.get(User, user["id"])
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "cpf" in updates:
        cpf = normalize_cpf(updates.pop("cpf"))
        if cpf:
            if not is_valid_cpf(cpf):
                raise HTTPException(status_code=400, detail="CPF inválido. Verifique os números digitados.")
            dup = db.query(User).filter(User.cpf == cpf, User.id != fresh.id).first()
            if dup:
                raise HTTPException(status_code=400, detail="Este CPF já está cadastrado.")
            fresh.cpf = cpf
    for k, v in updates.items():
        setattr(fresh, k, v)
    db.commit()
    db.refresh(fresh)
    return _public(fresh)


@router.put("/password")
def change_password(payload: PasswordChangeInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    fresh = db.get(User, user["id"])
    if not verify_password(payload.current_password, fresh.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    fresh.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Senha atualizada"}


@router.get("/addresses")
def list_addresses(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    fresh = db.get(User, user["id"])
    return fresh.addresses or []


@router.post("/addresses")
def add_address(payload: Address, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    fresh = db.get(User, user["id"])
    addresses = list(fresh.addresses or [])
    new_addr = payload.model_dump()
    new_addr["id"] = str(uuid.uuid4())
    if new_addr.get("is_default") or not addresses:
        for a in addresses:
            a["is_default"] = False
        new_addr["is_default"] = True
    addresses.append(new_addr)
    fresh.addresses = addresses
    flag_modified(fresh, "addresses")
    db.commit()
    return addresses


@router.delete("/addresses/{address_id}")
def delete_address(address_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    fresh = db.get(User, user["id"])
    addresses = [a for a in (fresh.addresses or []) if a.get("id") != address_id]
    fresh.addresses = addresses
    flag_modified(fresh, "addresses")
    db.commit()
    return addresses
