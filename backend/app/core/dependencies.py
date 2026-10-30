
from bson import ObjectId
from fastapi import Depends, HTTPException, status
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
    current_user: dict = Depends(get_current_user)
):
    db = get_database()

    membership = db.workspace_members.find_one({
        "user_id": current_user["_id"],
        "is_active": True
    })

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
