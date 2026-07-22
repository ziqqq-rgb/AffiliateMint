from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(session: Session = Depends(get_session)):
    return get_dashboard_summary(session)