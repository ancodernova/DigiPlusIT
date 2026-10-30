from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.database import get_database
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.core.serialization import serialize_document


def register_user(data):
    db = get_database()
    email = data.email.lower().strip()

    if db.users.find_one({"email": email}):
        raise HTTPException(409, "Email already registered")

    now = datetime.now(timezone.utc)

    user = {
        "full_name": data.full_name,
        "email": email,
        "password_hash": hash_password(data.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }

    workspace = {
        "name": data.workspace_name,
        "workspace_type": "organization",
        "created_at": now,
        "created_by": None,
        "is_active": True
    }

    try:
        result = db.users.insert_one(user)
        user_id = result.inserted_id

        workspace["created_by"] = user_id
        workspace_result = db.workspaces.insert_one(workspace)
        workspace_id = workspace_result.inserted_id

        db.workspace_members.insert_one({
            "workspace_id": workspace_id,
            "user_id": user_id,
            "role": "admin",
            "is_active": True,
            "joined_at": now
        })

        token = create_access_token(str(user_id))

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": serialize_document({
                "_id": user_id,
                "full_name": user["full_name"],
                "email": email
            }),
            "workspace": serialize_document({
                "_id": workspace_id,
                "name": workspace["name"]
            })
        }

    except DuplicateKeyError:
        raise HTTPException(409, "Email already registered")

    except Exception:
        # Avoid leaving an orphan user if workspace creation fails.
        if "user_id" in locals():
            db.workspace_members.delete_many({"user_id": user_id})
            db.workspaces.delete_many({"created_by": user_id})
            db.users.delete_one({"_id": user_id})
        raise


def login_user(data):
    db = get_database()

    user = db.users.find_one({
        "email": data.email.lower().strip()
    })

    if not user or not verify_password(
        data.password,
        user["password_hash"]
    ):
        raise HTTPException(401, "Invalid email or password")

    if not user.get("is_active", False):
        raise HTTPException(403, "Account is disabled")

    memberships = list(db.workspace_members.find({
        "user_id": user["_id"],
        "is_active": True
    }).sort("joined_at", -1))

    if not memberships:
        raise HTTPException(403, "No active workspace found")

    workspace_ids = [membership["workspace_id"] for membership in memberships]
    workspaces = {
        workspace["_id"]: workspace
        for workspace in db.workspaces.find({
            "_id": {"$in": workspace_ids},
            "is_active": True
        })
    }

    # Prefer the user's own workspace over an invited workspace. Membership
    # order is only used as a deterministic fallback for shared workspaces.
    membership = next(
        (
            item for item in memberships
            if workspaces.get(item["workspace_id"], {}).get("created_by") == user["_id"]
        ),
        next((item for item in memberships if item["workspace_id"] in workspaces), None),
    )
    workspace = workspaces.get(membership["workspace_id"]) if membership else None

    if not workspace:
        raise HTTPException(403, "Workspace unavailable")

    return {
        "access_token": create_access_token(str(user["_id"])),
        "token_type": "bearer",
        "user": serialize_document({
            "_id": user["_id"],
            "full_name": user["full_name"],
            "email": user["email"]
        }),
        "workspace": serialize_document(workspace)
    }