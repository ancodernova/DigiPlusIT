from fastapi import APIRouter, Depends

from app.schemas.auth import RegisterRequest, LoginRequest
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