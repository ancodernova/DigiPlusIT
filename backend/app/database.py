
from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings


class MongoDB:
    client: MongoClient | None = None
    database: Database | None = None


mongodb = MongoDB()


def connect_to_mongodb():
    """Establish a connection to MongoDB Atlas."""
    mongodb.client = MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        appname="ContextFlowAI"
    )

    # Verify connectivity immediately.
    mongodb.client.admin.command("ping")

    mongodb.database = mongodb.client[settings.MONGODB_DATABASE]

    print("Connected to MongoDB Atlas successfully!")


def close_mongodb_connection():
    """Close MongoDB connection."""
    if mongodb.client:
        mongodb.client.close()
        mongodb.client = None
        mongodb.database = None


def get_database() -> Database:
    if mongodb.database is None:
        raise RuntimeError("MongoDB is not connected.")

    return mongodb.database
