from bson import ObjectId
from datetime import datetime, date
from typing import Any


def serialize_document(document: dict) -> dict:
    result = {}

    for key, value in document.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [
                serialize_document(item)
                if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item
                for item in value
            ]
        elif isinstance(value, dict):
            result[key] = serialize_document(value)
        else:
            result[key] = value

    return result