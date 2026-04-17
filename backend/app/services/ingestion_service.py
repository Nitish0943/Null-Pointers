from sqlalchemy.orm import Session
from ..db import models
from .twin_service import twin_service
from .analytics_service import analytics_service
from datetime import datetime

class IngestionService:
    async def process_telemetry(self, db: Session, data: dict):
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
        pred_pos = twin_service.predict_motor_position(data['steps'])
        pred_temp = twin_service.predict_temperature(data['pwm'])
        
        prediction = models.Prediction(
            predicted_position=pred_pos,
            predicted_temperature=pred_temp
        )
        db.add(prediction)
        db.commit()

        # 3. Analyze Deviations (Reality Gap)
        pos_err = data['position'] - pred_pos
        temp_err = data['temperature'] - pred_temp
        
        analysis = analytics_service.compute_risk(pos_err, temp_err)
        
        result = models.AnalysisResult(
            position_error=pos_err,
            temperature_error=temp_err,
            risk_score=analysis['risk_score'],
            issue_detected=analysis['issue_detected'],
            recommendation=analysis['recommendation']
        )
        db.add(result)
        db.commit()

        return {
            "telemetry": telemetry,
            "prediction": prediction,
            "analysis": result
        }

ingestion_service = IngestionService()
