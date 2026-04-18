import asyncio
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
from datetime import datetime, timedelta

async def background_recovery_monitor():
    """
    Routinely checks healing events marked as 'verifying'.
    Waits 20 seconds after action is sent, then checks if telemetry improved.
    """
    while True:
        await asyncio.sleep(10)
        db = SessionLocal()
        try:
            # Find all open events older than 15 seconds
            threshold_time = datetime.utcnow() - timedelta(seconds=15)
            open_events = db.query(models.HealingEvent).filter(
                models.HealingEvent.verification_status == "verifying",
                models.HealingEvent.timestamp < threshold_time
            ).all()

            for event in open_events:
                # Get the average position/temperature error before the event
                before_period_start = event.timestamp - timedelta(seconds=30)
                before_analysis = db.query(models.AnalysisResult).filter(
                    models.AnalysisResult.timestamp >= before_period_start,
                    models.AnalysisResult.timestamp < event.timestamp
                ).all()

                # Get average after the event
                after_analysis = db.query(models.AnalysisResult).filter(
                    models.AnalysisResult.timestamp > event.timestamp
                ).all()

                if len(before_analysis) == 0 or len(after_analysis) == 0:
                    continue # Not enough data yet

                avg_temp_err_before = sum([a.temperature_error for a in before_analysis]) / len(before_analysis)
                avg_temp_err_after = sum([a.temperature_error for a in after_analysis]) / len(after_analysis)

                avg_pos_err_before = sum([a.position_error for a in before_analysis]) / len(before_analysis)
                avg_pos_err_after = sum([a.position_error for a in after_analysis]) / len(after_analysis)

                # Check if improvement occurred (errors reduced by 20% or flatlined near zero)
                temp_improved = avg_temp_err_after < (avg_temp_err_before * 0.8) or avg_temp_err_after < 2.0
                pos_improved = avg_pos_err_after < (avg_pos_err_before * 0.8) or avg_pos_err_after < 2.0

                improvement_happened = temp_improved or pos_improved
                
                # Check for active anomalies completely vanishing
                still_anomalous = any(a.anomaly_flag for a in after_analysis[-5:])

                if improvement_happened and not still_anomalous:
                    event.verification_status = "recovered"
                else:
                    event.verification_status = "escalated"
                
                event.recovery_time_sec = (datetime.utcnow() - event.timestamp).total_seconds()
                db.commit()

        except Exception as e:
            print(f"[Recovery Monitor] Error: {e}")
        finally:
            db.close()
