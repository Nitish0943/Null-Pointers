import numpy as np
import math
from typing import Dict, Any

class AnalyticsService:
    def __init__(self):
        # Thresholds
        self.POS_THRESHOLD = 0.5   # mm
        self.TEMP_THRESHOLD = 15.0  # Celsius
        
        # Z-Score settings
        self.Z_CRITICAL = 3.0  # 3-sigma
        
    def calculate_z_score(self, current_val: float, history: list) -> float:
        """
        Calculates how many standard deviations the current value is from the mean.
        """
        if len(history) < 10:
            return 0.0
            
        mean = np.mean(history)
        std = np.std(history)
        
        if std == 0:
            return 0.0
            
        return abs((current_val - mean) / std)

    def compute_risk(self, pos_error: float, temp_error: float) -> Dict[str, Any]:
        """
        Aggregated Risk Scoring Logic based on reality gap.
        """
        abs_pos_err = abs(pos_error)
        abs_temp_err = abs(temp_error)
        
        # Normalize errors into a 0-1 risk score components
        # We assume 1.0mm pos error or 25C temp error as "Full Scale Risk"
        pos_risk = min(1.0, abs_pos_err / 1.0)
        temp_risk = min(1.0, abs_temp_err / 25.0)
        
        # Combined risk (Weighted: Temperature is often more critical for safety)
        risk_score = (pos_risk * 0.4) + (temp_risk * 0.6)
        
        issue_detected = False
        recommendation = "System Nominal"
        
        # Decision Logic
        if abs_temp_err > self.TEMP_THRESHOLD:
            issue_detected = True
            recommendation = "CRITICAL: Thermal runaway or sensor failure detected!"
            risk_score = max(risk_score, 0.9)
        elif abs_pos_err > self.POS_THRESHOLD:
            issue_detected = True
            recommendation = "WARNING: Motor lead-screw friction or step loss detected."
            risk_score = max(risk_score, 0.6)
        elif risk_score > 0.4:
            recommendation = "NOTICE: System performance drifting from twin model."
            
        return {
            "risk_score": round(float(risk_score), 2),
            "issue_detected": issue_detected,
            "recommendation": recommendation
        }

analytics_service = AnalyticsService()

