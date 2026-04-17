"""
feature_mapping.py — Domain Feature Mapping

Maps between NASA CMAPSS feature space and our Motor-Heater twin feature space.

Why this is needed:
  - The CMAPSS dataset uses absolute sensor readings (e.g., sensor_2 ≈ 641°R)
  - Our system works with ERRORS (deviation from twin prediction)
  - We normalize CMAPSS into [0,1] and treat as "relative error magnitude proxies"

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
import math


def map_cmapss_to_twin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts preprocessed CMAPSS features into twin error space.
    
    Input columns expected: 'temp_signal', 'pos_signal', 'pwm_signal' (all 0-1 normalized)
    Output columns:          'position_error', 'temperature_error', 'pwm_norm'
    
    The interpretation:
    - A high temp_signal  → system ran hot → maps to a temperature_error proxy
    - A high pos_signal   → mechanical load / pressure rise → maps to position error
    - pwm_signal          → control input as fraction of max duty cycle
    """
    mapped = pd.DataFrame()

    # Scale to realistic error magnitudes for our system
    # position_error range: 0 to ~1.5 mm
    mapped["position_error"] = df["pos_signal"] * 1.5

    # temperature_error range: 0 to ~25°C
    mapped["temperature_error"] = df["temp_signal"] * 25.0

    # PWM as fraction (0-1)
    mapped["pwm_norm"] = df["pwm_signal"]

    return mapped


def generate_twin_data(n_samples: int = 2000) -> pd.DataFrame:
    """
    Augmentation Generator: Simulates motor-heater digital twin behavior.
    
    Simulates:
    1. Normal motor movement with small position noise
    2. Exponential temperature heating curve (T = k * (1 - e^(-lambda*t)))
    3. PWM control schedule cycling between 30% and 80%
    4. Artificial fault events (10% of samples) with high errors
    
    Returns a DataFrame in our native error space:
      position_error, temperature_error, pwm_norm
    """
    rng = np.random.default_rng(seed=99)
    t = np.linspace(0, 60, n_samples)  # 60 seconds of simulation

    # === Normal Behavior ===
    # Position: Linear motion with small Gaussian noise (expected error ≈ 0)
    pos_error_normal = 0.05 + rng.normal(0, 0.03, n_samples)

    # Temperature: Exponential approach from 25°C → 45°C, with noise
    k_lambda = 0.08  # Heating constant
    temp_rise = 20.0 * (1 - np.exp(-k_lambda * t))  # max 20°C rise
    temp_error_normal = np.abs(rng.normal(0, 0.8, n_samples))  # small random error

    # PWM: Duty cycle cycling 30%→80%→30% over time
    pwm_cycle = 0.55 + 0.25 * np.sin(2 * np.pi * t / 30)
    pwm_norm = np.clip(pwm_cycle + rng.normal(0, 0.02, n_samples), 0, 1)

    # === Fault Events (10% of samples) ===
    fault_mask = rng.random(n_samples) < 0.10
    pos_error_normal[fault_mask] += rng.uniform(0.6, 1.5, fault_mask.sum())   # motor drift
    temp_error_normal[fault_mask] += rng.uniform(8.0, 20.0, fault_mask.sum()) # thermal spike

    # Clip negatives (errors are absolute magnitudes)
    pos_error = np.abs(pos_error_normal)
    temp_error = np.abs(temp_error_normal)

    df = pd.DataFrame({
        "position_error": pos_error,
        "temperature_error": temp_error,
        "pwm_norm": pwm_norm
    })

    print(f"[FeatureMapper] ✓ Generated {n_samples} twin simulation samples")
    return df


def to_feature_vector(position_error: float, temperature_error: float, pwm: int) -> np.ndarray:
    """
    Converts a real-time telemetry error reading into the feature vector
    expected by the Isolation Forest model.
    
    Args:
        position_error:    |actual_pos - predicted_pos| in mm
        temperature_error: |actual_temp - predicted_temp| in °C
        pwm:               motor control signal (0-255)

    Returns:
        numpy array shape (1, 3)
    """
    pwm_norm = pwm / 255.0  # Normalize PWM to [0, 1]

    return np.array([[
        float(position_error),
        float(temperature_error),
        float(pwm_norm)
    ]])
