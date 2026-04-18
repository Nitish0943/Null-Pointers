from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db import models
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/monthly-loss")
async def get_monthly_loss(db: Session = Depends(get_db)):
    """
    Calculates cumulative production loss for the current month.
    """
    first_day = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats = db.query(
        func.sum(models.ProductionLoss.units_lost).label("total_units"),
        func.sum(models.ProductionLoss.cost_loss_inr).label("total_cost")
    ).filter(models.ProductionLoss.timestamp >= first_day).first()
    
    return {
        "status": "ok",
        "month": datetime.utcnow().strftime("%B %Y"),
        "total_units_lost": stats.total_units or 0,
        "total_cost_loss_inr": stats.total_cost or 0.0
    }

@router.post("/loss")
async def calculate_loss_override(payload: dict, db: Session = Depends(get_db)):
    """
    Manual override endpoint to calculate loss for a specific scenario.
    """
    try:
        from app.agents.loss_engine import loss_engine
        # Mocking input for engine
        ml_mock = {"anomaly": True}
        rca_mock = {"severity": payload.get("severity", "MEDIUM")}
        
        result = loss_engine.process(db, ml_mock, rca_mock, machine_id=payload.get("machine_id", "manual_check"))
        if result:
            return {"status": "ok", "loss_metrics": result}
        raise HTTPException(status_code=400, detail="Calculation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
