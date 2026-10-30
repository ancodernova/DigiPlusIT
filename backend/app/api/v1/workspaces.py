"""Workspace and team routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user, get_current_workspace, object_id, require_roles
from app.core.serialization import serialize_document
from app.database import get_database
from app.schemas.workspace import MemberRoleUpdate, TeamCreate, TeamUpdate, WorkspaceCreate, WorkspaceUpdate
from app.schemas.activity import MemberAdd

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/")
def list_workspaces(user=Depends(get_current_user)):
    db = get_database()
    memberships = db.workspace_members.find({"user_id": user["_id"], "is_active": True})
    ids = [item["workspace_id"] for item in memberships]
    return [serialize_document(x) for x in db.workspaces.find({"_id": {"$in": ids}, "is_active": True})]


@router.post("/", status_code=201)
def create_workspace(data: WorkspaceCreate, user=Depends(get_current_user)):
    db, now = get_database(), datetime.now(timezone.utc)
    result = db.workspaces.insert_one({"name": data.name, "workspace_type": data.workspace_type, "created_by": user["_id"], "is_active": True, "created_at": now})
    db.workspace_members.insert_one({"workspace_id": result.inserted_id, "user_id": user["_id"], "role": "admin", "is_active": True, "joined_at": now})
    return serialize_document(db.workspaces.find_one({"_id": result.inserted_id}))


@router.get("/current")
def current(context=Depends(get_current_workspace)):
    return serialize_document(context["workspace"])


@router.patch("/current")
def update_current(data: WorkspaceUpdate, context=Depends(require_roles("admin"))):
    get_database().workspaces.update_one({"_id": context["workspace"]["_id"]}, {"$set": {"name": data.name}})
    return {"name": data.name}


@router.get("/teams")
def list_teams(context=Depends(get_current_workspace)):
    return [serialize_document(x) for x in get_database().teams.find({"workspace_id": context["workspace"]["_id"]})]


@router.post("/teams", status_code=201)
def create_team(data: TeamCreate, context=Depends(require_roles("admin", "manager"))):
    doc = {**data.model_dump(), "workspace_id": context["workspace"]["_id"], "created_by": context["user"]["_id"], "created_at": datetime.now(timezone.utc)}
    try:
        result = get_database().teams.insert_one(doc)
    except Exception as exc:
        raise HTTPException(409, "Team already exists") from exc
    return serialize_document(get_database().teams.find_one({"_id": result.inserted_id}))


@router.patch("/teams/{team_id}")
def update_team(team_id: str, data: TeamUpdate, context=Depends(require_roles("admin", "manager"))):
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    result = get_database().teams.update_one({"_id": object_id(team_id, "team ID"), "workspace_id": context["workspace"]["_id"]}, {"$set": updates})
    if not result.matched_count: raise HTTPException(404, "Team not found")
    return serialize_document(get_database().teams.find_one({"_id": object_id(team_id)}))


@router.delete("/teams/{team_id}")
def delete_team(team_id: str, context=Depends(require_roles("admin"))):
    result = get_database().teams.delete_one({"_id": object_id(team_id, "team ID"), "workspace_id": context["workspace"]["_id"]})
    if not result.deleted_count:
        raise HTTPException(404, "Team not found")
    return {"deleted": True}


@router.get("/members")
def list_members(context=Depends(get_current_workspace)):
    db = get_database()
    members = list(db.workspace_members.find({"workspace_id": context["workspace"]["_id"], "is_active": True}))
    users = {u["_id"]: u for u in db.users.find({"_id": {"$in": [m["user_id"] for m in members]}})}
    return [{"user": serialize_document(users.get(m["user_id"], {})), "membership": serialize_document(m)} for m in members]


@router.post("/members", status_code=201)
def add_member(data: MemberAdd, context=Depends(require_roles("admin"))):
    db, email = get_database(), data.email.lower().strip()
    user = db.users.find_one({"email": email, "is_active": True})
    if not user:
        raise HTTPException(404, "User account not found; registration is required first")
    if db.workspace_members.find_one({"workspace_id": context["workspace"]["_id"], "user_id": user["_id"]}):
        raise HTTPException(409, "User is already a workspace member")
    now = datetime.now(timezone.utc)
    db.workspace_members.insert_one({"workspace_id": context["workspace"]["_id"], "user_id": user["_id"], "role": data.role, "is_active": True, "joined_at": now})
    return {"user_id": str(user["_id"]), "role": data.role}


@router.get("/teams/{team_id}")
def get_team(team_id: str, context=Depends(get_current_workspace)):
    item = get_database().teams.find_one({"_id": object_id(team_id, "team ID"), "workspace_id": context["workspace"]["_id"]})
    if not item:
        raise HTTPException(404, "Team not found")
    return serialize_document(item)


@router.patch("/members/{user_id}")
def change_member_role(user_id: str, data: MemberRoleUpdate, context=Depends(require_roles("admin"))):
    db, uid = get_database(), object_id(user_id, "user ID")
    membership = db.workspace_members.find_one({"workspace_id": context["workspace"]["_id"], "user_id": uid, "is_active": True})
    if not membership:
        raise HTTPException(404, "Member not found")
    if membership["role"] == "admin" and data.role != "admin" and db.workspace_members.count_documents({"workspace_id": context["workspace"]["_id"], "role": "admin", "is_active": True}) <= 1:
        raise HTTPException(409, "Cannot remove the last workspace admin")
    db.workspace_members.update_one({"_id": membership["_id"]}, {"$set": {"role": data.role}})
    return {"user_id": user_id, "role": data.role}


@router.delete("/members/{user_id}")
def remove_member(user_id: str, context=Depends(require_roles("admin"))):
    db, uid = get_database(), object_id(user_id, "user ID")
    membership = db.workspace_members.find_one({"workspace_id": context["workspace"]["_id"], "user_id": uid, "is_active": True})
    if not membership:
        raise HTTPException(404, "Member not found")
    if membership["role"] == "admin" and db.workspace_members.count_documents({"workspace_id": context["workspace"]["_id"], "role": "admin", "is_active": True}) <= 1:
        raise HTTPException(409, "Cannot remove the last workspace admin")
    db.workspace_members.update_one({"_id": membership["_id"]}, {"$set": {"is_active": False}})
    return {"removed": True}
