"""Transcript ingestion and retrieval routes."""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.dependencies import get_current_workspace
from app.schemas.transcript import TranscriptPasteRequest
from app.services import transcription_service

router = APIRouter(prefix="/transcripts", tags=["Transcripts"])


@router.post("/paste", status_code=201)
def paste_transcript(data: TranscriptPasteRequest, context=Depends(get_current_workspace)):
    return transcription_service.create_paste(data, context)


@router.post("/upload", status_code=202)
async def upload_transcript(
    file: UploadFile = File(...),
    meeting_id: str | None = Form(default=None),
    language: str | None = Form(default=None),
    context=Depends(get_current_workspace),
):
    allowed_types = {
        "txt": {"text/plain"},
        "vtt": {"text/vtt", "text/plain"},
        "srt": {"application/x-subrip", "text/plain"},
        "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "pdf": {"application/pdf"},
        "mp3": {"audio/mpeg", "audio/mp3"},
        "wav": {"audio/wav", "audio/x-wav"},
        "m4a": {"audio/mp4", "audio/x-m4a"},
    }
    filename = file.filename or ""
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in allowed_types or (file.content_type and file.content_type not in allowed_types[suffix]):
        from fastapi import HTTPException
        raise HTTPException(415, "File extension and MIME type are not supported")
    content = await file.read()
    return transcription_service.create_upload_job(file.filename or "upload", content, context, meeting_id, language)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, context=Depends(get_current_workspace)):
    return transcription_service.get_job(job_id, context)


@router.get("/{transcript_id}")
def get_transcript(transcript_id: str, context=Depends(get_current_workspace)):
    return transcription_service.get_transcript(transcript_id, context)
