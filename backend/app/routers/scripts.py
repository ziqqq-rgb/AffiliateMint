from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import ContentCard, ScriptVariation
from app.services.pipeline import edit_script, get_scripts_for_product, select_script, start_scripting

router = APIRouter(prefix="/scripts", tags=["scripts"])


class ScriptUpdateRequest(BaseModel):
    hook_ms: str | None = None
    body_ms: str | None = None
    cta_ms: str | None = None
    caption_ms: str | None = None
    visual_notes: str | None = None


@router.post("/{dossier_id}/generate", response_model=list[ScriptVariation])
def generate(dossier_id: int, session: Session = Depends(get_session)):
    try:
        return start_scripting(session, dossier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/product/{product_id}", response_model=list[ScriptVariation])
def list_for_product(product_id: int, session: Session = Depends(get_session)):
    return get_scripts_for_product(session, product_id)


@router.put("/{script_id}", response_model=ScriptVariation)
def update(script_id: int, body: ScriptUpdateRequest, session: Session = Depends(get_session)):
    """Point 3: hand-edit a generated script; feeds the edit into Hermes' memory."""
    try:
        return edit_script(session, script_id, body.dict(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{script_id}/select", response_model=ContentCard)
def select(script_id: int, session: Session = Depends(get_session)):
    try:
        return select_script(session, script_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))