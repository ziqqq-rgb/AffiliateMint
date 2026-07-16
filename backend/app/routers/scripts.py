"""HTTP layer for the script-writing stage - Approval Gate 2 (FR-3.5, FR-3.6)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import ContentCard, ScriptVariation
from app.services.pipeline import select_script, start_scripting

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.post("/{dossier_id}/generate", response_model=list[ScriptVariation])
def generate(dossier_id: int, session: Session = Depends(get_session)):
    try:
        return start_scripting(session, dossier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{script_id}/select", response_model=ContentCard)
def select(script_id: int, session: Session = Depends(get_session)):
    try:
        return select_script(session, script_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
