
from pymongo import ASCENDING, DESCENDING, TEXT

from app.database import get_database


COLLECTIONS = [
    "users",
    "workspaces",
    "workspace_members",
    "teams",
    "meetings",
    "decisions",
    "tasks",
    "task_history",
    "task_meeting_links",
    "knowledge_documents",
    "context_passports",
    "activity_logs",
    "notifications",
]


def initialize_database():
    db = get_database()

    existing = set(db.list_collection_names())

    for collection in COLLECTIONS:
        if collection not in existing:
            db.create_collection(collection)
            print(f"Created collection: {collection}")

    # USERS
    db.users.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="unique_user_email"
    )

    # WORKSPACES
    db.workspaces.create_index(
        [("created_by", ASCENDING)]
    )

    # WORKSPACE MEMBERS
    db.workspace_members.create_index(
        [("workspace_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True
    )

    db.workspace_members.create_index(
        [("user_id", ASCENDING)]
    )

    # TEAMS
    db.teams.create_index(
        [("workspace_id", ASCENDING), ("name", ASCENDING)],
        unique=True
    )

    # MEETINGS
    db.meetings.create_index(
        [("workspace_id", ASCENDING), ("meeting_date", DESCENDING)]
    )

    db.meetings.create_index(
        [("workspace_id", ASCENDING), ("team_id", ASCENDING)]
    )

    # DECISIONS
    db.decisions.create_index(
        [("workspace_id", ASCENDING), ("meeting_id", ASCENDING)]
    )

    # TASKS
    db.tasks.create_index(
        [("workspace_id", ASCENDING), ("status", ASCENDING)]
    )

    db.tasks.create_index(
        [("workspace_id", ASCENDING), ("owner_id", ASCENDING)]
    )

    db.tasks.create_index(
        [("workspace_id", ASCENDING), ("due_date", ASCENDING)]
    )

    db.tasks.create_index(
        [("source_meeting_id", ASCENDING)]
    )

    db.tasks.create_index(
        [("title", TEXT), ("description", TEXT)],
        name="task_search_index"
    )

    # TASK HISTORY
    db.task_history.create_index(
        [("task_id", ASCENDING), ("created_at", DESCENDING)]
    )

    # TASK MEETING LINKS
    db.task_meeting_links.create_index(
        [("task_id", ASCENDING), ("meeting_id", ASCENDING)],
        unique=True
    )

    # KNOWLEDGE DOCUMENTS
    db.knowledge_documents.create_index(
        [("workspace_id", ASCENDING), ("created_at", DESCENDING)]
    )

    db.knowledge_documents.create_index(
        [("title", TEXT), ("content", TEXT)],
        name="knowledge_search_index"
    )

    # CONTEXT PASSPORTS
    db.context_passports.create_index(
        [("workspace_id", ASCENDING), ("created_at", DESCENDING)]
    )

    # ACTIVITY LOGS
    db.activity_logs.create_index(
        [("workspace_id", ASCENDING), ("created_at", DESCENDING)]
    )

    # NOTIFICATIONS
    db.notifications.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)]
    )

    db.notifications.create_index(
        [("user_id", ASCENDING), ("read", ASCENDING)]
    )

    print("\nContextFlow AI database initialized successfully!")
    print(f"Collections created/verified: {len(COLLECTIONS)}")
    print("Indexes created/verified.")
