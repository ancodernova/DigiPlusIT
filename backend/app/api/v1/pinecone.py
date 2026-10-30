"""Protected Pinecone diagnostics."""

from fastapi import APIRouter, Depends

from app.core.dependencies import require_roles
from app.services.pinecone_service import validate_index_dimension

router = APIRouter(prefix="/pinecone", tags=["Pinecone"])


@router.get("/status")
def status(context=Depends(require_roles("admin"))):
    return validate_index_dimension()
