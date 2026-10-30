"""Groq Whisper transcription and transcript persistence."""

import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException

from app.config import settings
from app.core.dependencies import object_id
from app.core.serialization import serialize_document
from app.database import get_database
from app.services.indexing_service import index_record, mark_indexing_failed

logger = logging.getLogger(__name__)
SUPPORTED_AUDIO = {"mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "ogg", "webm", "flac"}
SUPPORTED_TEXT = {"txt", "vtt", "srt", "docx", "pdf"}


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_paste(data, context):
    db, now = get_database(), datetime.now(timezone.utc)
    digest = _hash(data.transcript_text.encode("utf-8"))
    existing = db.transcripts.find_one({"workspace_id": context["workspace"]["_id"], "content_hash": digest})
    if existing:
        return serialize_document(existing)
    meeting_id = object_id(data.meeting_id, "meeting ID") if data.meeting_id else None
    if meeting_id and not db.meetings.find_one({"_id": meeting_id, "workspace_id": context["workspace"]["_id"]}):
        raise HTTPException(404, "Meeting not found")
    document = {"workspace_id": context["workspace"]["_id"], "meeting_id": meeting_id, "source": "manual_paste", "title": data.title, "original_text": data.transcript_text, "language": data.language, "participants": [object_id(x, "participant ID") for x in data.participants], "metadata": data.metadata, "content_hash": digest, "status": "transcribed", "created_by": context["user"]["_id"], "created_at": now, "updated_at": now}
    result = db.transcripts.insert_one(document)
    saved = db.transcripts.find_one({"_id": result.inserted_id})
    try:
        index_record("transcripts", saved, saved["original_text"], "transcript")
    except Exception as exc:
        mark_indexing_failed("transcripts", saved["_id"], exc)
    return serialize_document(db.transcripts.find_one({"_id": result.inserted_id}))


def create_upload_job(file_name: str, content: bytes, context, meeting_id=None, language=None):
    suffix = Path(file_name).suffix.lower().lstrip(".")
    if suffix not in SUPPORTED_AUDIO | SUPPORTED_TEXT:
        raise HTTPException(415, "Unsupported transcript file type")
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(413, "Uploaded file exceeds the configured size limit")
    now = datetime.now(timezone.utc)
    job_id = get_database().transcript_jobs.insert_one({"workspace_id": context["workspace"]["_id"], "meeting_id": object_id(meeting_id, "meeting ID") if meeting_id else None, "job_type": "transcription", "status": "queued", "progress": 0, "attempts": 0, "error": None, "created_by": context["user"]["_id"], "created_at": now, "updated_at": now}).inserted_id
    path = Path(settings.LOCAL_STORAGE_PATH) / str(context["workspace"]["_id"]) / f"{job_id}.{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    get_database().transcript_jobs.update_one({"_id": job_id}, {"$set": {"source_file_reference": str(path), "original_filename": Path(file_name).name}})
    process_job(job_id, path, suffix, context, language)
    return serialize_document(get_database().transcript_jobs.find_one({"_id": job_id}))


def process_job(job_id, path: Path, suffix: str, context, language=None):
    db, now = get_database(), datetime.now(timezone.utc)
    db.transcript_jobs.update_one({"_id": job_id}, {"$set": {"status": "transcribing", "progress": 25, "updated_at": now}, "$inc": {"attempts": 1}})
    try:
        if suffix in {"txt", "vtt", "srt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            source = "file_upload"
        elif suffix == "docx":
            from docx import Document
            text = "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
            source = "file_upload"
        elif suffix == "pdf":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            source = "file_upload"
        else:
            text = groq_transcribe(path, language)
            source = "file_upload"
        digest = _hash(text.encode("utf-8"))
        transcript = {"workspace_id": context["workspace"]["_id"], "meeting_id": db.transcript_jobs.find_one({"_id": job_id}).get("meeting_id"), "source": source, "title": path.name, "original_text": text, "language": language, "participants": [], "content_hash": digest, "status": "transcribed", "source_file_reference": str(path), "created_by": context["user"]["_id"], "created_at": now, "updated_at": now}
        transcript_id = db.transcripts.update_one({"workspace_id": transcript["workspace_id"], "content_hash": digest}, {"$setOnInsert": transcript}, upsert=True).upserted_id
        if transcript_id is None:
            transcript_id = db.transcripts.find_one({"workspace_id": transcript["workspace_id"], "content_hash": digest})["_id"]
        db.transcript_jobs.update_one({"_id": job_id}, {"$set": {"status": "completed", "progress": 100, "transcript_id": transcript_id, "updated_at": datetime.now(timezone.utc)}})
    except Exception as exc:
        logger.exception("Transcript job failed", extra={"job_id": str(job_id)})
        db.transcript_jobs.update_one({"_id": job_id}, {"$set": {"status": "failed", "error": "Transcript processing failed", "updated_at": datetime.now(timezone.utc)}})


def groq_transcribe(path: Path, language=None) -> str:
    if not settings.GROQ_API_KEY:
        raise HTTPException(503, "Transcription provider is not configured")
    from groq import Groq
    started = time.monotonic()
    with path.open("rb") as audio:
        response = Groq(api_key=settings.GROQ_API_KEY).audio.transcriptions.create(file=(path.name, audio), model=settings.GROQ_TRANSCRIPTION_MODEL, language=language, response_format="verbose_json", timeout=settings.REQUEST_TIMEOUT_SECONDS)
    logger.info("Transcription completed", extra={"model": settings.GROQ_TRANSCRIPTION_MODEL, "duration_ms": round((time.monotonic() - started) * 1000)})
    return response.text


def get_transcript(transcript_id, context):
    item = get_database().transcripts.find_one({"_id": object_id(transcript_id, "transcript ID"), "workspace_id": context["workspace"]["_id"]})
    if not item:
        raise HTTPException(404, "Transcript not found")
    return serialize_document(item)


def get_job(job_id, context):
    item = get_database().transcript_jobs.find_one({"_id": object_id(job_id, "job ID"), "workspace_id": context["workspace"]["_id"]})
    if not item:
        raise HTTPException(404, "Transcript job not found")
    return serialize_document(item)
