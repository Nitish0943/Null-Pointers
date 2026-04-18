from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import models
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class TimeMachine:
    def process(self, db: Session, ml_result: Dict[str, Any], rca_result: Dict[str, Any], machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Generates past event replay and future risk projection.
        """
        if not ml_result.get("anomaly", False):
            return None

        past_events = self._generate_past_replay(db, machine_id)
        future_projections = self._generate_future_simulation(ml_result, rca_result)

        return {
            "past_events": past_events,
            "future_if_ignored": future_projections
        }

    def _generate_past_replay(self, db: Session, machine_id: str) -> List[str]:
        """
        Analyzes the last 20 telemetry/analysis records to identify the sequence of failure.
        """
        # Get last 20 analysis results
        history = db.query(models.AnalysisResult)\
            .filter(models.AnalysisResult.source == machine_id)\
            .order_by(desc(models.AnalysisResult.timestamp))\
            .limit(20)\
            .all()
        
        # We want to iterate in chronological order for the timeline
        history.reverse()

        events = []
        for i, entry in enumerate(history):
            time_str = entry.timestamp.strftime("%H:%M:%S")
            
            # Identify "first points" of specific failures
            if entry.anomaly_flag and len(events) < 5:
                if entry.temperature_error > 5 and "Temperature rise detected" not in str(events):
                    events.append(f"{time_str} Temperature rise began")
                if entry.position_error > 0.1 and "Position lag detected" not in str(events):
                    events.append(f"{time_str} Position lag increased")
                if entry.risk_score > 0.5 and "Risk threshold crossed" not in str(events):
                    events.append(f"{time_str} Risk score spiked (>0.5)")

        # Fallback if history is too short or clean
        if len(events) < 2:
            events.append(f"{datetime.utcnow().strftime('%H:%M:%S')} Anomaly pattern identified")
            events.append(f"{datetime.utcnow().strftime('%H:%M:%S')} Root cause mapping complete")

        return events[-5:] # Return top 5 most relevant steps

    def _generate_future_simulation(self, ml_result: Dict[str, Any], rca_result: Dict[str, Any]) -> List[str]:
        """
        Simulates future state based on current severity and risk growth.
        """
        severity = rca_result.get("severity", "LOW").upper()
        current_risk = ml_result.get("risk_score", 0.0)
        
        # Growth factors based on severity
        growth_map = {
            "CRITICAL": {"risk": 0.08, "temp": 5},
            "HIGH": {"risk": 0.05, "temp": 3},
            "MEDIUM": {"risk": 0.03, "temp": 1.5},
            "LOW": {"risk": 0.01, "temp": 0.5}
        }
        
        factors = growth_map.get(severity, growth_map["LOW"])
        projections = []
        
        # +2 mins
        proj_risk_2 = min(1.0, current_risk + (factors["risk"] * 2))
        projections.append(f"+2 min Risk = {proj_risk_2:.2f}")
        
        # +4 mins
        proj_risk_4 = min(1.0, current_risk + (factors["risk"] * 4))
        projections.append(f"+4 min Critical thresholds exceeded")
        
        # +6 mins
        if severity in ["CRITICAL", "HIGH"]:
            projections.append(f"+6 min Emergency stop likely")
        else:
            projections.append(f"+6 min System performance degradation")
            
        return projections

time_machine = TimeMachine()
