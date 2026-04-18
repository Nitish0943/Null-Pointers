from sqlalchemy.orm import Session
from app.db import models
from typing import Dict, Any, Optional
from datetime import datetime

class LossEngine:
    def __init__(self):
        # Operational parameters (can be moved to a settings table later)
        self.MACHINE_OUTPUT_PER_MIN = 2.5
        self.COST_PER_UNIT_INR = 75.0
        
        # Severity to downtime mapping (in minutes)
        self.severity_downtime = {
            "CRITICAL": 30,
            "HIGH": 15,
            "MEDIUM": 8,
            "LOW": 3
        }

    def process(self, db: Session, ml_result: Dict[str, Any], rca_result: Dict[str, Any], machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Calculates production loss based on anomaly detection and RCA results.
        """
        if not ml_result.get("anomaly", False):
            return None

        severity = rca_result.get("severity", "LOW").upper()
        downtime = self.severity_downtime.get(severity, 5)
        
        units_lost = int(downtime * self.MACHINE_OUTPUT_PER_MIN)
        cost_loss = float(units_lost * self.COST_PER_UNIT_INR)
        
        urgency = "High" if severity in ["CRITICAL", "HIGH"] else "Medium"
        priority = "Immediate" if severity == "CRITICAL" else ("Normal" if severity == "HIGH" else "Scheduled")

        try:
            loss_entry = models.ProductionLoss(
                machine_id=machine_id,
                estimated_downtime_min=downtime,
                units_lost=units_lost,
                cost_loss_inr=cost_loss,
                urgency=urgency,
                recovery_priority=priority
            )
            db.add(loss_entry)
            db.commit()
            db.refresh(loss_entry)
            
            return {
                "estimated_downtime": f"{downtime} min",
                "units_lost": units_lost,
                "cost_loss_inr": cost_loss,
                "urgency": urgency,
                "recovery_priority": priority
            }
        except Exception as e:
            print(f"[LossEngine] Error: {e}")
            db.rollback()
            return None

loss_engine = LossEngine()
