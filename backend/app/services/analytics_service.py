import numpy as np
from typing import Dict, Any

class AnalyticsService:
    def __init__(self):
        self.threshold_z = 3.0  # 3-sigma rule
        self.drift_threshold = 5.0  # Celsius/mm deviation for drift
        
    def detect_anomalies(self, actual: float, predicted: float, history: list) -> Dict[str, Any]:
        """
        Z-Score Anomaly Detection
        """
        if not history:
            return {"is_anomaly": False, "score": 0.0}
            
        errors = [h['actual'] - h['predicted'] for h in history]
        mean_err = np.mean(errors)
        std_err = np.std(errors) if len(errors) > 1 else 1.0
        
        current_err = actual - predicted
        z_score = abs((current_err - mean_err) / std_err) if std_err > 0 else 0.0
        
        return {
            "is_anomaly": z_score > self.threshold_z,
            "score": float(z_score)
        }

    def compute_risk(self, pos_error: float, temp_error: float) -> Dict[str, Any]:
        """
        Aggregated Risk Scoring Logic
        """
        # Normalize errors into a 0-1 risk score
        risk_score = min(1.0, (abs(pos_error) / 10.0 + abs(temp_error) / 20.0) / 2.0)
        
        issue_detected = False
        recommendation = "System Nominal"
        
        if risk_score > 0.8:
            issue_detected = True
            recommendation = "CRITICAL: Immediate shutdown recommended. External resistance detected."
        elif risk_score > 0.5:
            issue_detected = True
            recommendation = "WARNING: System drifting. Check mechanical friction and heater ventilation."
            
        return {
            "risk_score": float(risk_score),
            "issue_detected": issue_detected,
            "recommendation": recommendation
        }

analytics_service = AnalyticsService()
