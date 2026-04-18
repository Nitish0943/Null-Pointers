from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models

router = APIRouter()

@router.get("/list")
async def list_tickets(db: Session = Depends(get_db), limit: int = 50):
    """Fetch the latest maintenance tickets."""
    tickets = db.query(models.MaintenanceTicket).order_by(models.MaintenanceTicket.timestamp.desc()).limit(limit).all()
    return {"status": "ok", "tickets": tickets}

@router.post("/create")
async def create_ticket(payload: dict, db: Session = Depends(get_db)):
    """Manual ticket creation override."""
    try:
        from app.agents.maintenance_engine import maintenance_engine
        # Simulate RCA output format to reuse mapping logic
        rca_mock = {"root_cause": payload.get("issue", "Unknown Issue")}
        ml_mock = {"anomaly": True}
        
        ticket = maintenance_engine.process(db, ml_mock, rca_mock, active_source=payload.get("machine_id", "manual"))
        if ticket:
            return {"status": "created", "ticket": ticket}
        raise HTTPException(status_code=400, detail="Failed to create ticket")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
