from typing import Dict, Optional, Tuple

class ActionPolicy:
    """
    Defines the safety boundaries and maps root causes to safe, reversible hardware actions.
    """
    ALLOWED_ACTIONS = [
        "none",
        "reduce_speed",
        "reduce_pwm",
        "pause_motor",
        "enable_cooling",
        "recalibrate_sensor",
        "emergency_stop",
        "notify_operator"
    ]

    @staticmethod
    def evaluate_action(
        root_cause: str,
        pos_error: float,
        temp_error: float,
        severity: str,
        current_pwm: int
    ) -> Tuple[str, Optional[int], str]:
        """
        Determines the safest action.
        Returns: (action_name, action_value, reasoning_layer)
        """
        # 1. Critical Overrides
        if severity == "CRITICAL" or temp_error > 25.0:
            return "emergency_stop", 0, "Critical threshold crossed. Initiating immediate halt."

        # 2. Temperature Anomalies
        if "Overheating" in root_cause or "thermal" in root_cause.lower():
            if temp_error > 10.0:
                # Safe PWM reduction
                new_pwm = max(50, current_pwm - 50) 
                return "reduce_pwm", new_pwm, "Thermal runaway detected. Reducing PWM safely to offset temperature."
            else:
                return "enable_cooling", 1, "Mild thermal variance. Auxiliary cooling flagged."

        # 3. Mechanical / Positional Anomalies
        if "friction" in root_cause.lower() or "Mechanical" in root_cause:
            if pos_error > 5.0:
                return "pause_motor", 0, "High friction + position drift. Pausing motor briefly to reset tension."
            else:
                # Reduce speed by lowering PWM slightly
                new_pwm = max(100, current_pwm - 20)
                return "reduce_speed", new_pwm, "Positional drag detected. Lowering operational speed."

        # 4. Sensor Issues
        if "sensor" in root_cause.lower() or "drift" in root_cause.lower():
            return "recalibrate_sensor", 1, "Sensor noise or drift. Issuing soft-recalibration."

        # Default fallback
        return "none", None, "No safe action required. Monitoring."
