from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models

router = APIRouter()

@router.get("/history")
def get_healing_history(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch recent autonomous healing events from the ML action engine."""
    events = db.query(models.HealingEvent).order_by(models.HealingEvent.timestamp.desc()).limit(limit).all()
    return events

@router.get("/status")
def get_healing_status(db: Session = Depends(get_db)):
    """Fetch the status of the single most recent intervention."""
    event = db.query(models.HealingEvent).order_by(models.HealingEvent.timestamp.desc()).first()
    if not event:
        return {"status": "standby"}
    return {
        "status": event.verification_status,
        "action": event.action_taken,
        "issue": event.anomaly_detected,
        "timestamp": event.timestamp
    }
