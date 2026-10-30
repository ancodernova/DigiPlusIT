from fastapi import APIRouter, Depends, HTTPException

from app.schemas.auth import LoginRequest, PasswordChangeRequest, ProfileUpdateRequest, RegisterRequest
from app.database import get_database
from app.core.security import hash_password, verify_password
from app.services.auth_service import register_user, login_user
from app.core.dependencies import get_current_user
from app.core.serialization import serialize_document

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(data: RegisterRequest):
    return register_user(data)


@router.post("/login")
def login(data: LoginRequest):
    return login_user(data)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return serialize_document({
        "_id": user["_id"],
        "full_name": user["full_name"],
        "email": user["email"]
    })


@router.patch("/me")
def update_profile(data: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    get_database().users.update_one({"_id": user["_id"]}, {"$set": {"full_name": data.full_name}})
    return {"full_name": data.full_name, "email": user["email"]}


@router.post("/change-password")
def change_password(data: PasswordChangeRequest, user: dict = Depends(get_current_user)):
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    get_database().users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": hash_password(data.new_password)}})
    return {"message": "Password changed successfully"}