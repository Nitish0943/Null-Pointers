from sqlalchemy.orm import Session
from .action_policy import ActionPolicy
from app.db import models
from typing import Dict, Any

class SelfHealingEngine:
    def __init__(self):
        self.policy = ActionPolicy()
    
    def process(
        self, 
        db: Session,
        telemetry: Dict[str, Any],
        ml_result: Dict[str, Any],
        rca_result: Dict[str, Any],
        pos_error: float,
        temp_error: float
    ) -> Dict[str, Any]:
        """
        Evaluate the pipeline output and determine if an autonomous intervention is needed.
        """
        # If no anomaly flag, or it's just minor noise, skip healing
        if not ml_result.get("anomaly", False):
            return {
                "issue_detected": False,
                "action": "none",
                "status": "nominal"
            }

        root_cause = rca_result.get("root_cause", "Unknown Anomaly")
        severity = rca_result.get("severity", "LOW")
        confidence = rca_result.get("confidence_score", 0.0)

        # Let the policy determine the safest action
        action_name, action_value, reasoning = self.policy.evaluate_action(
            root_cause=root_cause,
            pos_error=pos_error,
            temp_error=temp_error,
            severity=severity,
            current_pwm=telemetry.get("pwm", 0)
        )

        if action_name == "none":
            return {
                "issue_detected": True,
                "action": "none",
                "status": "watching"
            }

        # Issue command block
        command_sent = True
        
        # Log to History for Reinforcement Learning later
        event = models.HealingEvent(
            anomaly_detected=root_cause,
            action_taken=action_name,
            action_value=action_value,
            confidence=confidence,
            command_sent=command_sent,
            verification_status="verifying"
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        return {
            "healing_id": event.id,
            "issue_detected": True,
            "root_cause": root_cause,
            "selected_action": action_name,
            "action_value": action_value,
            "command_sent": command_sent,
            "verification_status": "verifying",
            "confidence": confidence,
            "reasoning": reasoning
        }

self_healing_engine = SelfHealingEngine()
