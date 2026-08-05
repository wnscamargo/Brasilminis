import uuid

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from db import db
from deps import get_current_user
from models import ProfileInput, PasswordChangeInput, Address
from security import hash_password, verify_password

router = APIRouter(prefix="/api/account", tags=["account"])


@router.put("/profile")
async def update_profile(payload: ProfileInput, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": updates})
    fresh = await db.users.find_one({"_id": ObjectId(user["id"])})
    return {
        "id": user["id"],
        "name": fresh.get("name"),
        "email": fresh.get("email"),
        "role": fresh.get("role"),
        "phone": fresh.get("phone", ""),
        "newsletter": fresh.get("newsletter", False),
    }


@router.put("/password")
async def change_password(payload: PasswordChangeInput, user: dict = Depends(get_current_user)):
    fresh = await db.users.find_one({"_id": ObjectId(user["id"])})
    if not verify_password(payload.current_password, fresh["password_hash"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"password_hash": hash_password(payload.new_password)}},
    )
    return {"message": "Senha atualizada"}


@router.get("/addresses")
async def list_addresses(user: dict = Depends(get_current_user)):
    fresh = await db.users.find_one({"_id": ObjectId(user["id"])})
    return fresh.get("addresses", [])


@router.post("/addresses")
async def add_address(payload: Address, user: dict = Depends(get_current_user)):
    fresh = await db.users.find_one({"_id": ObjectId(user["id"])})
    addresses = fresh.get("addresses", [])
    new_addr = payload.model_dump()
    new_addr["id"] = str(uuid.uuid4())
    if new_addr.get("is_default") or not addresses:
        for a in addresses:
            a["is_default"] = False
        new_addr["is_default"] = True
    addresses.append(new_addr)
    await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"addresses": addresses}})
    return addresses


@router.delete("/addresses/{address_id}")
async def delete_address(address_id: str, user: dict = Depends(get_current_user)):
    fresh = await db.users.find_one({"_id": ObjectId(user["id"])})
    addresses = [a for a in fresh.get("addresses", []) if a.get("id") != address_id]
    await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"addresses": addresses}})
    return addresses
