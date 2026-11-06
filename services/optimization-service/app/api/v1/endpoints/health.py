from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from shared.api_contracts.responses import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        service="optimization-service",
        version="0.1.0",
        database="n/a",
    )

@router.get("/ready", response_model=HealthResponse)
def readiness_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {str(exc)}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        service="optimization-service",
        version="0.1.0",
        database=db_status,
    )
