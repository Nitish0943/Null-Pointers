"""
feature_mapping.py — Domain Feature Mapping (v2 — Clean)

Maps between NASA CMAPSS feature space and our Motor-Heater twin feature space.

v2 Changes (ML Fix Phase 1):
  - REMOVED fault injection from generate_twin_data() — training must be pure normal
  - Tightened normal distributions to match real system behavior (0-2°C, 0-0.15mm)
  - Added separate generate_fault_data() for use in model validation only
  - Renamed generate_twin_data → generate_normal_twin_data for clarity

Mapping Table:
  ┌─────────────────────┬──────────────────────────────┬──────────────────────┐
  │ CMAPSS Feature      │ Physical Meaning              │ Our System Variable  │
  ├─────────────────────┼──────────────────────────────┼──────────────────────┤
  │ sensor_2 (norm)     │ Temperature rise proxy        │ temperature_error    │
  │ sensor_7 (norm)     │ Mechanical stress proxy       │ position_error       │
  │ os_3 (norm)         │ Control duty cycle proxy      │ pwm (normalized)     │
  └─────────────────────┴──────────────────────────────┴──────────────────────┘
"""

import numpy as np
import pandas as pd


def map_cmapss_to_twin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts preprocessed CMAPSS features into twin error space.
    Input:  'temp_signal', 'pos_signal', 'pwm_signal' (all 0-1 normalized)
    Output: 'position_error', 'temperature_error', 'pwm_norm'

    Scale is constrained to realistic normal operating ranges:
      position_error: 0 → 0.15 mm  (normal  is < 0.15mm)
      temperature_error: 0 → 2.5°C (normal  is < 2.5°C)
    """
    mapped = pd.DataFrame()

    # Scale to TIGHT realistic normal ranges — NOT the fault range
    # This is the critical fix for Problem 1: training distribution was 10x too wide
    mapped["position_error"]    = df["pos_signal"]  * 0.15   # 0 → 0.15 mm (normal op)
    mapped["temperature_error"] = df["temp_signal"] * 2.5    # 0 → 2.5°C (normal op)
    mapped["pwm_norm"]          = df["pwm_signal"]            # 0 → 1 (unchanged)

    return mapped


def generate_normal_twin_data(n_samples: int = 2000) -> pd.DataFrame:
    """
    Generates PURE NORMAL digital twin operating data for training.

    v2 change: ZERO fault injection. All samples represent healthy operation.
    The model learns strictly what normal looks like so any deviation stands out.

    Distributions calibrated to match real motor-heater system:
      - position_error: small Gaussian around 0.05mm (normal stepping noise)
      - temperature_error: small Gaussian around 0.5°C (thermostat hunt)
      - pwm_norm: realistic PWM cycling 30%–70%
    """
    rng = np.random.default_rng(seed=99)
    t = np.linspace(0, 60, n_samples)

    # Normal position error: tight around 0.05 mm, max ~0.15 mm
    # (motor stepping noise, no drift)
    pos_error = np.abs(rng.normal(loc=0.05, scale=0.02, size=n_samples))
    pos_error = np.clip(pos_error, 0.0, 0.15)

    # Normal temperature error: tight around 0.5°C
    # (thermocouple noise, PID hunt is ±1°C max in healthy state)
    temp_error = np.abs(rng.normal(loc=0.5, scale=0.3, size=n_samples))
    temp_error = np.clip(temp_error, 0.0, 2.5)

    # PWM: realistic duty cycle cycling 30% → 70% → 30%
    pwm_norm = 0.5 + 0.20 * np.sin(2 * np.pi * t / 30)
    pwm_norm = np.clip(pwm_norm + rng.normal(0, 0.02, n_samples), 0.3, 0.7)

    df = pd.DataFrame({
        "position_error":    pos_error,
        "temperature_error": temp_error,
        "pwm_norm":          pwm_norm,
    })

    print(f"[FeatureMapper] ✓ Generated {n_samples} NORMAL twin training samples")
    print(f"[FeatureMapper]   pos_error   range: {pos_error.min():.4f}–{pos_error.max():.4f} mm")
    print(f"[FeatureMapper]   temp_error  range: {temp_error.min():.4f}–{temp_error.max():.4f} °C")
    return df


def generate_fault_data(n_samples: int = 300) -> pd.DataFrame:
    """
    Generates KNOWN FAULT samples for model validation only.
    NOT used in training — only used in evaluate_model() to measure fault recall.

    Fault types included:
      1. Thermal runaway: temp_error 15–25°C
      2. Motor jam: pos_error 0.8–1.5mm, high current (pwm near max)
      3. Step loss: pos_error 0.5–1.2mm, normal temp
      4. Combined fault: both errors elevated
    """
    rng = np.random.default_rng(seed=777)
    n_each = n_samples // 4

    # Type 1: Thermal runaway
    t1 = pd.DataFrame({
        "position_error":    rng.uniform(0.01, 0.10, n_each),
        "temperature_error": rng.uniform(15.0, 25.0, n_each),
        "pwm_norm":          rng.uniform(0.3, 0.7, n_each),
    })

    # Type 2: Mechanical jam
    t2 = pd.DataFrame({
        "position_error":    rng.uniform(0.8, 1.5, n_each),
        "temperature_error": rng.uniform(0.3, 2.0, n_each),
        "pwm_norm":          rng.uniform(0.7, 1.0, n_each),
    })

    # Type 3: Step loss
    t3 = pd.DataFrame({
        "position_error":    rng.uniform(0.5, 1.2, n_each),
        "temperature_error": rng.uniform(0.2, 1.5, n_each),
        "pwm_norm":          rng.uniform(0.3, 0.6, n_each),
    })

    # Type 4: Combined fault
    t4 = pd.DataFrame({
        "position_error":    rng.uniform(0.6, 1.3, n_samples - 3 * n_each),
        "temperature_error": rng.uniform(10.0, 20.0, n_samples - 3 * n_each),
        "pwm_norm":          rng.uniform(0.5, 0.9, n_samples - 3 * n_each),
    })

    fault_df = pd.concat([t1, t2, t3, t4], ignore_index=True)
    print(f"[FeatureMapper] ✓ Generated {len(fault_df)} fault samples for validation")
    return fault_df


def to_feature_vector(position_error: float, temperature_error: float, pwm: int) -> np.ndarray:
    """
    Converts a real-time telemetry error reading into the feature vector
    expected by the Isolation Forest model.

    Args:
        position_error:    |actual_pos  - predicted_pos|  (mm)
        temperature_error: |actual_temp - predicted_temp| (°C)
        pwm:               motor control signal (0-255)

    Returns:
        numpy array shape (1, 3)
    """
    pwm_norm = pwm / 255.0

    return np.array([[
        float(position_error),
        float(temperature_error),
        float(pwm_norm),
    ]])


# Backward compatibility alias (used by old model.py calls)
generate_twin_data = generate_normal_twin_data
