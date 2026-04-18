from sqlalchemy.orm import Session
from app.db import models
from typing import Dict, Any, Optional
import uuid

class MaintenanceEngine:
    def __init__(self):
        # Base mapping rules for autonomous ticketing
        self.ruleset = {
            "overheating": {
                "part": "Heater Relay & Thermal Paste",
                "eta": "45 min",
                "downtime": "Immediate / Emergency Stop",
                "priority": "Critical"
            },
            "thermal": {
                "part": "Auxiliary Cooling Fan",
                "eta": "15 min",
                "downtime": "Next idle cycle",
                "priority": "High"
            },
            "friction": {
                "part": "Lead Screw Bearing / Lubricant",
                "eta": "20 min",
                "downtime": "Next idle cycle",
                "priority": "High"
            },
            "mechanical": {
                "part": "Stepper Motor Assembly",
                "eta": "90 min",
                "downtime": "End of Shift",
                "priority": "Medium"
            },
            "sensor": {
                "part": "Optical Encoder",
                "eta": "10 min",
                "downtime": "Live Swap Possible",
                "priority": "Low"
            },
            "calibration": {
                "part": "Software / Firmware Update",
                "eta": "5 min",
                "downtime": "No Shutdown Required",
                "priority": "Low"
            }
        }

    def _match_rules(self, root_cause: str) -> Dict[str, str]:
        rc_lower = root_cause.lower()
        for key, rules in self.ruleset.items():
            if key in rc_lower:
                return rules
        return {
            "part": "General Inspection Required",
            "eta": "TBD",
            "downtime": "TBD",
            "priority": "Medium"
        }

    def process(self, db: Session, ml_result: Dict[str, Any], rca_result: Dict[str, Any], active_source: str, loss_metrics: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluate if a ticket should be generated based on ML and RCA output.
        Returns ticket dictionary if generated, else None.
        """
        if not ml_result.get("anomaly", False):
            return None

        root_cause = rca_result.get("root_cause", "Unknown Anomaly")
        severity = rca_result.get("severity", "LOW")
        
        rules = self._match_rules(root_cause)
        ticket_id = f"MT-{str(uuid.uuid4())[:6].upper()}"

        try:
            ticket = models.MaintenanceTicket(
                ticket_id=ticket_id,
                machine_id=active_source,
                priority=rules["priority"],
                issue=root_cause,
                recommended_part=rules["part"],
                repair_eta=rules["eta"],
                downtime_window=rules["downtime"],
                status="Open",
                severity=severity,
                loss_estimate_inr=loss_metrics.get("cost_loss_inr", 0.0) if loss_metrics else 0.0
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            return {
                "ticket_id": ticket.ticket_id,
                "machine_id": ticket.machine_id,
                "priority": ticket.priority,
                "issue": ticket.issue,
                "recommended_part": ticket.recommended_part,
                "repair_eta": ticket.repair_eta,
                "downtime_window": ticket.downtime_window,
                "status": ticket.status,
                "severity": ticket.severity,
                "loss_estimate_inr": ticket.loss_estimate_inr
            }
        except Exception as e:
            print(f"[MaintenanceEngine] Failed to generate ticket: {e}")
            db.rollback()
            return None

maintenance_engine = MaintenanceEngine()
