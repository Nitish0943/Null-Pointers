"""
inference.py — Real-Time ML Inference Engine (v2)

v2 Changes (ML Fix Phase 2):
  - Replaced hardcoded magic numbers (0.3, 0.6) with dynamic score normalization
    using the ACTUAL score range calibrated from training data (stored in metadata.json)
  - Score range is loaded once at module import and cached in memory for speed
"""

import numpy as np
from typing import Dict, Any

from .model import train_model
from .feature_mapping import to_feature_vector
from .metadata import get_score_range

# ── Model lazy-load cache ──────────────────────────────────────────────────────
_model  = None
_scaler = None
_score_min: float = -0.3   # Fallback until model loads
_score_max: float =  0.3


def _get_model():
    """
    Lazy loader — trains/loads model on first call, then caches in memory.
    Also loads the calibrated score range from metadata.json.
    """
    global _model, _scaler, _score_min, _score_max

    if _model is None or _scaler is None:
        _model, _scaler = train_model()
        # Load score range calibrated from training (Phase 2 fix)
        _score_min, _score_max = get_score_range()
        print(f"[Inference] Score range loaded: [{_score_min:.4f}, {_score_max:.4f}]")

    return _model, _scaler


def predict_anomaly(
    position_error:    float,
    temperature_error: float,
    pwm:               int,
) -> Dict[str, Any]:
    """
    Core inference function for real-time anomaly detection.

    v2 Score Normalization Fix:
      OLD (wrong): np.clip((-raw_score + 0.3) / 0.6, 0.0, 1.0)
        — 0.3 and 0.6 were guesses, not measured from the model

      NEW (correct): (score_max - raw_score) / (score_max - score_min)
        — denominator spans the REAL training score range
        — raw_score = score_max → anomaly_score = 0 (most normal)
        — raw_score = score_min → anomaly_score = 1 (most abnormal)
        — scores below score_min (extreme faults) → clipped to 1.0

    Args:
        position_error:    |actual_pos  - predicted_pos|  (mm)
        temperature_error: |actual_temp - predicted_temp| (°C)
        pwm:               control signal (0-255)

    Returns:
        dict: anomaly, anomaly_score, risk_score, issue_detected, recommendation
    """
    model, scaler = _get_model()

    # Build and scale feature vector
    X_raw    = to_feature_vector(position_error, temperature_error, pwm)
    X_scaled = scaler.transform(X_raw)

    # ── Isolation Forest Prediction ────────────────────────────────────────────
    raw_label = model.predict(X_scaled)[0]      # +1=normal, -1=anomaly
    is_anomaly = (raw_label == -1)

    raw_score = model.decision_function(X_scaled)[0]  # higher = more normal

    # ── Dynamic Score Normalization (Phase 2 fix) ──────────────────────────────
    score_range = _score_max - _score_min
    if score_range > 0:
        anomaly_score = (_score_max - raw_score) / score_range
    else:
        # Degenerate case: flat model (shouldn't happen with good training data)
        anomaly_score = 0.5

    anomaly_score = float(np.clip(anomaly_score, 0.0, 1.0))

    # ── Physics-Based Error Component ──────────────────────────────────────────
    # Provides deterministic risk floor — large real errors are always flagged
    # even if the ML model is uncertain
    pos_risk   = min(1.0, abs(position_error)    / 1.0)   # Full scale at 1.0 mm
    temp_risk  = min(1.0, abs(temperature_error) / 25.0)  # Full scale at 25°C

    physics_score = (pos_risk * 0.40) + (temp_risk * 0.60)

    # ── Combined Risk Score ────────────────────────────────────────────────────
    # ML (40%) + Physics (60%): physics is weighted higher — it's deterministic
    risk_score = float((anomaly_score * 0.40) + (physics_score * 0.60))
    risk_score = round(min(1.0, risk_score), 3)

    # ── Recommendations ───────────────────────────────────────────────────────
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
        "anomaly":        bool(is_anomaly),
        "anomaly_score":  round(anomaly_score, 3),
        "risk_score":     risk_score,
        "issue_detected": bool(issue_detected),
        "recommendation": recommendation,
    }
