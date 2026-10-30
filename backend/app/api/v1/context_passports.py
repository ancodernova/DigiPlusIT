"""Context Passport routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.core.dependencies import get_current_workspace
from app.schemas.passport import PassportGenerateRequest
from app.services import context_passport_service

router = APIRouter(prefix="/context-passports", tags=["Context Passports"])


@router.post("/generate", status_code=201)
def generate(data: PassportGenerateRequest, context=Depends(get_current_workspace)):
    return context_passport_service.generate_passport(data, context)


@router.get("/")
def list_all(context=Depends(get_current_workspace)):
    return context_passport_service.list_passports(context)


@router.get("/{passport_id}")
def get_one(passport_id: str, context=Depends(get_current_workspace)):
    return context_passport_service.get_passport(passport_id, context)


@router.get("/{passport_id}/markdown", response_class=PlainTextResponse)
def export_markdown(passport_id: str, context=Depends(get_current_workspace)):
    return context_passport_service.markdown(context_passport_service.get_passport(passport_id, context))


@router.post("/{passport_id}/regenerate")
def regenerate(passport_id: str, context=Depends(get_current_workspace)):
    passport = context_passport_service.get_passport(passport_id, context)
    from app.schemas.passport import PassportGenerateRequest
    return context_passport_service.generate_passport(
        PassportGenerateRequest(title=passport["title"], meeting_ids=[str(item) for item in passport.get("source_meeting_ids", [])]),
        context,
    )
