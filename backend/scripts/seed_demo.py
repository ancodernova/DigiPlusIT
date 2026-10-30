"""Seed an isolated, idempotent ContextFlow demonstration workspace.

Usage:
    DEMO_PASSWORD='local-only-password' python scripts/seed_demo.py

The script only writes records belonging to the deterministic demo workspace.
It never deletes or changes records outside that workspace.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from hashlib import md5
from pathlib import Path

from bson import ObjectId

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.database import close_mongodb_connection, connect_to_mongodb, get_database
from app.init_db import initialize_database
from app.services.indexing_service import index_record

DEMO_KEY = "contextflow-demo-workspace-v1"
DEMO_DOMAIN = "contextflowdemo.com"
PASSWORD_ENV = "DEMO_PASSWORD"

MEMBERS = [
    ("Asmiya Sayyed", "asmiya.sayyed", "admin"),
    ("Nidhi Patel", "nidhi.patel", "manager"),
    ("Saur Deshmukh", "saur.deshmukh", "manager"),
    ("Atharva Deokar", "atharva.deokar", "member"),
    ("Mira Kulkarni", "mira.kulkarni", "member"),
    ("Rohan Joshi", "rohan.joshi", "member"),
    ("Ishita Rao", "ishita.rao", "member"),
]

TRANSCRIPTS = [
    ("Product direction sync", "We aligned on a staged launch for the workspace assistant. Nidhi owns the rollout plan. Asmiya approved a two-week pilot with the support team."),
    ("Platform reliability review", "The API latency budget is at risk during transcript processing. Saur will profile Pinecone calls and Atharva will add request timing to the dashboard."),
    ("Customer discovery - Atlas", "Atlas needs searchable meeting history and clear task ownership. The team agreed that citations must link to the original meeting and document."),
    ("Design critique", "The navigation needs a clearer active state and the meeting capture flow should make consent explicit before upload."),
    ("Security review", "JWT cookies must remain HttpOnly. Workspace IDs must come from authorized membership and never from an LLM response."),
    ("Sprint planning", "The team selected transcript ingestion, task carry-forward, and Context Passport export as the sprint priorities."),
    ("Operations handover", "The next owner needs the current blockers, overdue tasks, and recent decisions in one grounded handover document."),
    ("Launch readiness", "The pilot is ready once the remaining blocked tasks are assigned and the Pinecone schema index has a successful retrieval smoke test."),
]


def stable_id(label: str) -> ObjectId:
    return ObjectId(md5(f"{DEMO_KEY}:{label}".encode()).hexdigest()[:24])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def seed(password: str, skip_pinecone: bool = False) -> dict:
    connect_to_mongodb()
    initialize_database()
    db = get_database()
    now = now_utc()
    workspace_id = stable_id("workspace")
    db.workspaces.update_one(
        {"demo_key": DEMO_KEY},
        {"$set": {"name": "ContextFlow AI Demo", "workspace_type": "organization", "is_active": True, "demo_key": DEMO_KEY, "updated_at": now},
         "$setOnInsert": {"_id": workspace_id, "created_at": now}},
        upsert=True,
    )
    workspace = db.workspaces.find_one({"demo_key": DEMO_KEY})
    workspace_id = workspace["_id"]

    users = {}
    for full_name, local_part, role in MEMBERS:
        user_id = stable_id(f"user:{local_part}")
        email = f"{local_part}@{DEMO_DOMAIN}"
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"full_name": full_name, "email": email, "is_active": True, "updated_at": now},
             "$setOnInsert": {"password_hash": hash_password(password), "created_at": now}},
            upsert=True,
        )
        user = db.users.find_one({"email": email})
        users[local_part] = user["_id"]
        db.workspace_members.update_one(
            {"workspace_id": workspace_id, "user_id": user["_id"]},
            {"$set": {"role": role, "is_active": True, "joined_at": now}},
            upsert=True,
        )

    teams = {}
    for name, description in (
        ("Product", "Product strategy and customer discovery"),
        ("Platform", "Backend reliability, AI, and data infrastructure"),
        ("Operations", "Launch readiness and team continuity"),
    ):
        team_id = stable_id(f"team:{name}")
        db.teams.update_one(
            {"_id": team_id},
            {"$set": {"workspace_id": workspace_id, "name": name, "description": description, "member_ids": list(users.values()), "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        teams[name] = team_id

    meetings = []
    for index, (title, transcript_text) in enumerate(TRANSCRIPTS):
        meeting_id = stable_id(f"meeting:{index}")
        meeting_date = now - timedelta(days=7 - index)
        document = {
            "_id": meeting_id, "workspace_id": workspace_id, "created_by": users["asmiya.sayyed"],
            "title": title, "description": f"Demo meeting for {title.lower()}",
            "meeting_type": "team_meeting", "team_id": teams["Platform" if index in (1, 4, 7) else "Product"],
            "agenda": "Review progress, decisions, risks, and next actions.",
            "raw_notes": transcript_text, "meeting_date": meeting_date,
            "participants": list(users.values())[:4 + index % 3], "status": "completed",
            "created_at": meeting_date, "updated_at": now,
        }
        db.meetings.replace_one({"_id": meeting_id}, document, upsert=True)
        transcript_id = stable_id(f"transcript:{index}")
        transcript = {
            "_id": transcript_id, "workspace_id": workspace_id, "meeting_id": meeting_id,
            "source": "demo_seed", "title": title, "original_text": transcript_text,
            "language": "en", "participants": document["participants"], "content_hash": md5(transcript_text.encode()).hexdigest(),
            "status": "completed", "created_by": users["asmiya.sayyed"], "created_at": meeting_date, "updated_at": now,
        }
        db.transcripts.replace_one({"_id": transcript_id}, transcript, upsert=True)
        meetings.append((meeting_id, transcript))
        decision_id = stable_id(f"decision:{index}")
        db.decisions.replace_one(
            {"_id": decision_id},
            {"_id": decision_id, "workspace_id": workspace_id, "meeting_id": meeting_id,
             "title": f"Approved outcome: {title}", "description": transcript_text.split(".")[0] + ".",
             "created_by": users["asmiya.sayyed"], "approved": True, "created_at": meeting_date},
            upsert=True,
        )

    statuses = ["open", "in_progress", "blocked", "completed"]
    priorities = ["low", "medium", "high", "critical"]
    tasks = []
    member_ids = list(users.values())
    for index in range(24):
        task_id = stable_id(f"task:{index}")
        due_date = now - timedelta(days=3) if index in (2, 9) else now + timedelta(days=index - 10)
        status = statuses[index % len(statuses)]
        task = {
            "_id": task_id, "workspace_id": workspace_id, "created_by": users["asmiya.sayyed"],
            "title": ["Prepare pilot rollout", "Profile vector search latency", "Assign launch owner", "Publish handover brief"][index % 4] + f" #{index + 1}",
            "description": "Demo task connected to the workspace continuity workflow.",
            "source_meeting_id": meetings[index % len(meetings)][0], "team_id": teams[["Product", "Platform", "Operations"][index % 3]],
            "owner_id": member_ids[index % len(member_ids)], "due_date": due_date,
            "priority": priorities[index % len(priorities)], "status": status,
            "carry_forward_count": 1 if index in (3, 7, 11) else 0,
            "created_at": now - timedelta(days=14 - index), "updated_at": now,
        }
        db.tasks.replace_one({"_id": task_id}, task, upsert=True)
        db.task_history.update_one(
            {"task_id": task_id, "event": "demo_seeded"},
            {"$set": {"workspace_id": workspace_id, "new_value": status, "created_by": users["asmiya.sayyed"], "created_at": now}},
            upsert=True,
        )
        tasks.append(task)

    for index, title in enumerate(("Pilot playbook", "Workspace search guidelines", "Security and privacy checklist", "Launch FAQ")):
        doc_id = stable_id(f"knowledge:{index}")
        content = f"{title}. This demo document explains the ContextFlow approach to grounded evidence, ownership, and workspace isolation."
        document = {"_id": doc_id, "workspace_id": workspace_id, "title": title, "content": content, "document_type": "guide",
                    "uploaded_by": users["asmiya.sayyed"], "created_at": now - timedelta(days=index), "updated_at": now}
        db.knowledge_documents.replace_one({"_id": doc_id}, document, upsert=True)

    for index in range(10):
        db.activity_logs.update_one(
            {"workspace_id": workspace_id, "demo_event": index},
            {"$set": {"workspace_id": workspace_id, "demo_event": index, "action": "demo_seeded", "entity_type": "workspace",
                      "entity_id": workspace_id, "actor_id": users["asmiya.sayyed"], "created_at": now - timedelta(hours=index)}},
            upsert=True,
        )
    for index, user_id in enumerate(member_ids[:5]):
        db.notifications.update_one(
            {"workspace_id": workspace_id, "demo_notification": index},
            {"$set": {"workspace_id": workspace_id, "demo_notification": index, "user_id": user_id,
                      "title": "Demo workspace update", "message": "A new grounded workspace record is available.",
                      "read": index % 2 == 0, "created_at": now - timedelta(hours=index)}},
            upsert=True,
        )

    passport_id = stable_id("passport")
    db.context_passports.replace_one(
        {"_id": passport_id},
        {"_id": passport_id, "workspace_id": workspace_id, "title": "Demo launch handover",
         "content": {"objective": "Run a safe pilot", "current_status": "active",
                     "important_decisions": [{"title": "Use a staged rollout"}],
                     "open_tasks": [{"title": "Assign launch owner"}],
                     "risks_and_blockers": [{"title": "Vector search latency"}],
                     "recommended_next_steps": [{"title": "Review the pilot playbook"}]},
         "source_meeting_ids": [meeting[0] for meeting in meetings], "source_task_ids": [task["_id"] for task in tasks],
         "generated_by": users["asmiya.sayyed"], "created_at": now},
        upsert=True,
    )

    indexed = 0
    if not skip_pinecone:
        for meeting_id, transcript in meetings:
            index_record("transcripts", transcript, transcript["original_text"], "transcript")
        for decision in db.decisions.find({"workspace_id": workspace_id}):
            index_record("decisions", decision, f"{decision['title']}\n{decision['description']}", "decision")
        for task in tasks:
            index_record("tasks", task, f"{task['title']}\n{task['description']}", "task")
        for document in db.knowledge_documents.find({"workspace_id": workspace_id}):
            index_record("knowledge_documents", document, document["content"], "knowledge_document")
        passport = db.context_passports.find_one({"_id": passport_id})
        index_record("context_passports", passport, str(passport["content"]), "context_passport")
        indexed = len(meetings) + len(tasks) + db.decisions.count_documents({"workspace_id": workspace_id}) + db.knowledge_documents.count_documents({"workspace_id": workspace_id}) + 1

    counts = {name: db[name].count_documents({"workspace_id": workspace_id}) for name in ("workspace_members", "teams", "meetings", "transcripts", "decisions", "tasks", "knowledge_documents", "activity_logs", "notifications", "context_passports")}
    return {"workspace_id": str(workspace_id), "demo_emails": [f"{local}@{DEMO_DOMAIN}" for _, local, _ in MEMBERS], "counts": counts, "pinecone_records_indexed": indexed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pinecone", action="store_true")
    args = parser.parse_args()
    password = os.getenv(PASSWORD_ENV)
    if not password or len(password) < 8:
        raise SystemExit(f"Set {PASSWORD_ENV} to a local password of at least 8 characters.")
    try:
        print(seed(password, args.skip_pinecone))
    finally:
        close_mongodb_connection()


if __name__ == "__main__":
    main()
