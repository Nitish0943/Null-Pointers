"""
inference.py — Real-Time ML Inference Engine

Provides the predict_anomaly() function used in the live telemetry pipeline.

How it works:
  1. Scale input features using the pre-trained StandardScaler
  2. Pass through Isolation Forest → raw anomaly score (decision_function)
  3. Convert score to normalized anomaly probability
  4. Combine ML score with physics-based error thresholds
  5. Output final risk_score, issue_detected, recommendation

Anomaly Score Interpretation:
  - decision_function() returns a value in roughly [-0.5, 0.5]
  - Negative values = anomalies (farther from training distribution)
  - Positive values = normal
  - We flip and normalize to [0, 1] for our risk score
"""

import numpy as np
from typing import Dict, Any

from .model import train_model
from .feature_mapping import to_feature_vector

# --- Lazy-load model on first inference ---
_model = None
_scaler = None


def _get_model():
    """
    Lazy loader — trains model on first call, then caches in memory.
    This avoids slow startup on import.
    """
    global _model, _scaler
    if _model is None or _scaler is None:
        _model, _scaler = train_model()
    return _model, _scaler


def predict_anomaly(
    position_error: float,
    temperature_error: float,
    pwm: int
) -> Dict[str, Any]:
    """
    Core inference function for real-time anomaly detection.

    Args:
        position_error:    Absolute deviation of actual vs predicted position (mm)
        temperature_error: Absolute deviation of actual vs predicted temperature (°C)
        pwm:               Current PWM signal (0-255)

    Returns:
        dict with:
          - anomaly (bool):        True if Isolation Forest flags this as anomalous
          - anomaly_score (float): Normalized measure of anomaly-ness (0=normal, 1=max anomalous)
          - risk_score (float):    Combined ML + physics risk (0-1)
          - issue_detected (bool): True if risk_score exceeds action threshold
          - recommendation (str):  Human-readable guidance string

    Example:
        >>> predict_anomaly(0.1, 2.0, 150)
        {'anomaly': False, 'anomaly_score': 0.12, 'risk_score': 0.08, ...}
        
        >>> predict_anomaly(1.2, 18.0, 200)
        {'anomaly': True, 'anomaly_score': 0.87, 'risk_score': 0.91, ...}
    """
    model, scaler = _get_model()

    # Build feature vector [position_error, temperature_error, pwm_norm]
    X_raw = to_feature_vector(position_error, temperature_error, pwm)

    # Scale using the training scaler
    X_scaled = scaler.transform(X_raw)

    # --- Isolation Forest Prediction ---
    # predict(): +1 = normal, -1 = anomaly
    raw_label = model.predict(X_scaled)[0]
    is_anomaly = (raw_label == -1)

    # decision_function(): negative = more anomalous, positive = more normal
    # Range is roughly [-0.5, 0.5] for typical models
    raw_score = model.decision_function(X_scaled)[0]

    # Normalize to [0, 1] anomaly probability
    # We clip raw_score to [-0.3, 0.3] and flip-scale
    # anomaly_score=1 means very anomalous, anomaly_score=0 means very normal
    anomaly_score = float(np.clip((-raw_score + 0.3) / 0.6, 0.0, 1.0))

    # --- Physics-Based Error Component ---
    # This ensures that large real errors are always flagged,
    # even if the ML model is uncertain
    pos_risk   = min(1.0, abs(position_error) / 1.0)    # Full scale at 1.0mm
    temp_risk  = min(1.0, abs(temperature_error) / 25.0) # Full scale at 25°C

    physics_score = (pos_risk * 0.40) + (temp_risk * 0.60)

    # --- Combined Risk Score ---
    # Blend ML anomaly score (40%) with physics-based score (60%)
    # Physics is weighted higher because it's directly interpretable
    risk_score = float((anomaly_score * 0.40) + (physics_score * 0.60))
    risk_score = round(min(1.0, risk_score), 3)

    # --- Issue Detection and Recommendations ---
    issue_detected = False
    recommendation = "System Nominal"

    if risk_score > 0.8 or (is_anomaly and physics_score > 0.5):
        issue_detected = True
        if abs(temperature_error) > 15.0:
            recommendation = (
                "CRITICAL: Thermal runaway detected. "
                "Check heater relay and temperature sensor."
            )
        elif abs(position_error) > 0.8:
            recommendation = (
                "CRITICAL: Severe motor position drift. "
                "Check lead screw, stepper driver, and limit switches."
            )
        else:
            recommendation = (
                "CRITICAL: ML model flagged abnormal system behavior. "
                "Initiate diagnostic sequence."
            )
    elif risk_score > 0.5 or is_anomaly:
        issue_detected = True
        recommendation = (
            "WARNING: System drifting from twin model. "
            "Monitor closely and inspect mechanical linkage."
        )
    elif risk_score > 0.3:
        recommendation = (
            "NOTICE: Minor deviation detected. "
            "System is within safe bounds but trending toward anomaly."
        )

    return {
        "anomaly":          bool(is_anomaly),
        "anomaly_score":    round(anomaly_score, 3),
        "risk_score":       risk_score,
        "issue_detected":   bool(issue_detected),
        "recommendation":   recommendation
    }
