
from bson import ObjectId
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_database
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    db = get_database()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")

        if not user_id or not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        user = db.users.find_one({
            "_id": ObjectId(user_id),
            "is_active": True
        })

        if not user:
            raise ValueError("User not found")

        return user

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_workspace(
    current_user: dict = Depends(get_current_user),
    workspace_header: str | None = Header(default=None, alias="X-Workspace-ID"),
):
    db = get_database()

    query = {"user_id": current_user["_id"], "is_active": True}
    if workspace_header:
        if not ObjectId.is_valid(workspace_header):
            raise HTTPException(status_code=400, detail="Invalid workspace ID")
        query["workspace_id"] = ObjectId(workspace_header)
    membership = db.workspace_members.find_one(query)

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="No active workspace membership found"
        )

    workspace = db.workspaces.find_one({
        "_id": membership["workspace_id"],
        "is_active": True
    })

    if not workspace:
        raise HTTPException(
            status_code=403,
            detail="Workspace not found or inactive"
        )

    return {
        "user": current_user,
        "workspace": workspace,
        "membership": membership
    }


def require_roles(*roles: str):
    def dependency(context: dict = Depends(get_current_workspace)):
        if context["membership"].get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient workspace permissions")
        return context

    return dependency


def object_id(value: str, label: str = "ID") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return ObjectId(value)
