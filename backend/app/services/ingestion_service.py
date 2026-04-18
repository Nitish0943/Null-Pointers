"""
ingestion_service.py — Main Telemetry Processing Pipeline

Full pipeline per telemetry event:
  1. Store raw telemetry to DB
  2. Run Digital Twin → get predicted values
  3. Compute Reality Gap (errors)
  4. Run ML Inference (Isolation Forest) → anomaly score + risk
  5. Run RCA Engine → root cause + confidence + reasoning
  6. Store combined analysis to DB
  7. Broadcast enriched payload over WebSocket
"""

import json
from sqlalchemy.orm import Session
from ..db import models
from .twin_service import twin_service
from .rca_engine import rca_engine
from ..ml.inference import predict_anomaly
from app.agents.notification_agent import notification_agent
from app.agents.self_healing_engine import self_healing_engine
from app.agents.maintenance_engine import maintenance_engine
from app.agents.loss_engine import loss_engine
from ..agents.orchestrator_agent import orchestrator
from datetime import datetime


class IngestionService:
    def __init__(self):
        self.manager = None  # WebSocket manager — injected by main.py on startup
        
        # Smoothing state (EMA filter)
        self.alpha = 0.4  # Smoothing factor (0.0 to 1.0; smaller = smoother but slower)
        self._smoothed_pos = None
        self._smoothed_temp = None

    async def process_telemetry(self, db: Session, data: dict, source: str = "simulated"):
        """
        Orchestrates the complete pipeline for a single telemetry event.

        Args:
            db:   SQLAlchemy session
            data: dict with keys: position, temperature, pwm, steps
                  (optionally: current — for ESP32 RCA analysis)

        Returns:
            dict with keys: telemetry, prediction, analysis
        """
        # ── 0. Smoothing (EMA Filter) ──────────────────────────────────────────
        # Fixes 'fluctuating' behavior by dampening sensor noise
        if self._smoothed_pos is None:
            self._smoothed_pos = data['position']
            self._smoothed_temp = data['temperature']
        else:
            self._smoothed_pos = (self.alpha * data['position']) + (1 - self.alpha) * self._smoothed_pos
            self._smoothed_temp = (self.alpha * data['temperature']) + (1 - self.alpha) * self._smoothed_temp
        
        # Use smoothed values for the rest of the pipeline
        clean_pos = round(self._smoothed_pos, 3)
        clean_temp = round(self._smoothed_temp, 2)

        # ── 1. Persist Raw/Smoothed Telemetry ──────────────────────────────────────────
        telemetry = models.TelemetryData(
            actual_position=data['position'],
            actual_temperature=data['temperature'],
            pwm=data['pwm'],
            steps=data['steps'],
            source=source
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

        # ── 2. Digital Twin Prediction ────────────────────────────────────────
        pred_pos  = twin_service.predict_motor_position(data['steps'])
        pred_temp = twin_service.predict_temperature(data['pwm'])

        # ── 3. Reality Gap (Physics Errors) ──────────────────────────────────
        pos_err  = clean_pos - pred_pos
        temp_err = clean_temp - pred_temp

        # Persist prediction
        prediction = models.Prediction(
            predicted_position=pred_pos,
            predicted_temperature=pred_temp
        )
        db.add(prediction)
        db.commit()

        # ── 4. ML Inference — Isolation Forest + Physics Risk Blend ──────────
        ml_result = predict_anomaly(
            position_error=abs(pos_err),
            temperature_error=abs(temp_err),
            pwm=data['pwm']
        )

        # ── 5. RCA Engine ─────────────────────────────────────────────────────
        # Estimate current from pwm if not directly provided (simulator fallback)
        current_amps = data.get('current', (data['pwm'] / 255.0) * 5.0)

        rca_result = rca_engine.analyze(
            actual={
                "position":    data['position'],
                "temperature": data['temperature'],
                "current":     current_amps,
            },
            predicted={
                "position":    pred_pos,
                "temperature": pred_temp,
            },
            pos_error=abs(pos_err),
            temp_error=abs(temp_err),
            anomaly_score=ml_result['anomaly_score'],
            pwm=data['pwm']
        )

        # ── 5b. Orchestrator — coordinates Monitoring, Explanation, Notification ──
        orchestrator_result = await orchestrator.run({
            "actual":      {"position": data['position'], "temperature": data['temperature'], "current": current_amps},
            "predicted":   {"position": pred_pos, "temperature": pred_temp},
            "ml_result":   ml_result,
            "rca_result":  rca_result,
            "pos_error":   abs(pos_err),
            "temp_error":  abs(temp_err),
        })
        # ── 5c. Self-Healing Engine ──
        healing_result = self_healing_engine.process(
            db, data, ml_result, rca_result, pos_err, temp_err
        )
        # ── 5d. Production Loss Estimation ──
        loss_metrics = loss_engine.process(
            db, ml_result, rca_result, machine_id=source
        )

        # ── 5e. Maintenance Ticket Generation ──
        maintenance_ticket = maintenance_engine.process(
            db, ml_result, rca_result, active_source=source, loss_metrics=loss_metrics
        )

        # ── 5f. AI Failure Time Machine (History Replay + Simulation) ──
        from app.agents.time_machine import time_machine
        failure_timeline = time_machine.process(
            db, ml_result, rca_result, machine_id=source
        )

        # ── 5g. Digital Twin talks like a Human ──
        from app.agents.machine_voice_engine import machine_voice_engine
        machine_voice = machine_voice_engine.generate_message(ml_result, rca_result)

        # ── 6. Persist Combined Analysis ──────────────────────────────────────
        result = models.AnalysisResult(
            position_error=pos_err,
            temperature_error=temp_err,
            risk_score=ml_result['risk_score'],
            issue_detected=ml_result['issue_detected'],
            recommendation=ml_result['recommendation'],
            anomaly_flag=ml_result['anomaly'],
            anomaly_score=ml_result['anomaly_score'],
            # RCA fields
            rca_root_cause=rca_result.get('root_cause', 'No Fault Detected'),
            rca_confidence=rca_result.get('confidence_score', 0.0),
            rca_severity=rca_result.get('severity', 'LOW'),
            rca_reasoning=json.dumps(rca_result.get('reasoning', [])),
            # Agent fields
            llm_explanation=(
                orchestrator_result["explanation"]["text"]
                if orchestrator_result.get("explanation") else None
            ),
            alert_state=orchestrator_result["monitoring"]["alert_state"],
            machine_voice=machine_voice,
            source=source,
        )
        db.add(result)
        db.commit()

        # ── 7. WebSocket Broadcast ────────────────────────────────────────────
        if self.manager:
            broadcast_data = {
                "type": "TELEMETRY_UPDATE",
                "data": {
                    "actual": {
                        "position":    clean_pos,
                        "temperature": clean_temp,
                        "pwm":         data['pwm'],
                        "steps":       data['steps'],
                        "source":      source,
                    },
                    "predicted": {
                        "position":    pred_pos,
                        "temperature": pred_temp,
                    },
                    "analysis": {
                        # ML & Error layer
                        "position_error": abs(pos_err),
                        "temperature_error": abs(temp_err),
                        "risk_score":     ml_result['risk_score'],
                        "anomaly":        ml_result['anomaly'],
                        "anomaly_score":  ml_result['anomaly_score'],
                        "issue_detected": ml_result['issue_detected'],
                        "recommendation": ml_result['recommendation'],
                        # RCA layer
                        "rca": {
                            "root_cause":          rca_result.get('root_cause'),
                            "confidence_score":    rca_result.get('confidence_score'),
                            "severity":            rca_result.get('severity'),
                            "reasoning":           rca_result.get('reasoning', []),
                            "recommended_action":  rca_result.get('recommended_action'),
                            "contributing_factors":rca_result.get('contributing_factors', []),
                        },
                        # Agent layer (NEW)
                        "agents": {
                            "alert_state":   orchestrator_result["monitoring"]["alert_state"],
                            "alert_event":   orchestrator_result["monitoring"]["alert_event"],
                            "risk_trend":    orchestrator_result["monitoring"]["risk_trend"],
                            "priority":      orchestrator_result["priority"],
                            "explanation":   orchestrator_result["explanation"]["text"] if orchestrator_result.get("explanation") else None,
                            "notified":      orchestrator_result["notification"]["sent"],
                            "healing":       healing_result,
                            "maintenance":   maintenance_ticket,
                            "loss_metrics":  loss_metrics,
                            "failure_timeline": failure_timeline,
                            "machineVoice":  machine_voice
                        }
                    }
                }
            }
            await self.manager.broadcast(broadcast_data)

        return {
            "telemetry":  telemetry,
            "prediction": prediction,
            "analysis":   result,
            "rca":        rca_result,      # Available for API response
            "healing":    healing_result,  # Let main.py send to ESP32
        }


ingestion_service = IngestionService()
