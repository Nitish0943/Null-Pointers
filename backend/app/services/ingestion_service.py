from sqlalchemy.orm import Session
from ..db import models
from .twin_service import twin_service
from ..ml.inference import predict_anomaly
from datetime import datetime


class IngestionService:
    def __init__(self):
        self.manager = None  # WebSocket manager — set by main.py

    async def process_telemetry(self, db: Session, data: dict):
        """
        Full pipeline:
          Telemetry → Digital Twin → Error Calculation → ML Inference → DB Storage → Broadcast
        """
        # 1. Store Raw Telemetry
        telemetry = models.TelemetryData(
            actual_position=data['position'],
            actual_temperature=data['temperature'],
            pwm=data['pwm'],
            steps=data['steps']
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

        # 2. Generate Digital Twin Prediction
        pred_pos  = twin_service.predict_motor_position(data['steps'])
        pred_temp = twin_service.predict_temperature(data['pwm'])

        prediction = models.Prediction(
            predicted_position=pred_pos,
            predicted_temperature=pred_temp
        )
        db.add(prediction)
        db.commit()

        # 3. Compute Reality Gap (Physics-based errors)
        pos_err  = data['position'] - pred_pos
        temp_err = data['temperature'] - pred_temp

        # 4. ML Inference — Isolation Forest + Physics Blended Risk
        ml_result = predict_anomaly(
            position_error=abs(pos_err),
            temperature_error=abs(temp_err),
            pwm=data['pwm']
        )

        # 5. Store Analysis Result (includes ML fields)
        result = models.AnalysisResult(
            position_error=pos_err,
            temperature_error=temp_err,
            risk_score=ml_result['risk_score'],
            issue_detected=ml_result['issue_detected'],
            recommendation=ml_result['recommendation'],
            anomaly_flag=ml_result['anomaly'],
            anomaly_score=ml_result['anomaly_score']
        )
        db.add(result)
        db.commit()

        # 6. Broadcast to frontend via WebSocket if connected
        if self.manager:
            broadcast_data = {
                "type": "TELEMETRY_UPDATE",
                "data": {
                    "actual": data,
                    "predicted": {
                        "position":    pred_pos,
                        "temperature": pred_temp
                    },
                    "analysis": {
                        "risk_score":    ml_result['risk_score'],
                        "anomaly":       ml_result['anomaly'],
                        "anomaly_score": ml_result['anomaly_score'],
                        "issue_detected":ml_result['issue_detected'],
                        "recommendation":ml_result['recommendation']
                    }
                }
            }
            await self.manager.broadcast(broadcast_data)

        return {
            "telemetry":  telemetry,
            "prediction": prediction,
            "analysis":   result
        }


ingestion_service = IngestionService()


