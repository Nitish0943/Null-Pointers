"""
model.py — Isolation Forest Training & Persistence

Uses scikit-learn's Isolation Forest for unsupervised anomaly detection.

Why Isolation Forest?
  - Works without labeled "fault" examples (we only have normal behavior)
  - Handles high-dimensional data with small samples
  - Lightweight, no GPU needed, real-time compatible
  - Explainable: anomaly score directly reflects outlier-ness

Training Strategy:
  1. Load CMAPSS normal samples (early cycles ≤ 100)
  2. Map to our error space (position_error, temperature_error, pwm_norm)
  3. Generate additional twin simulation data
  4. Combine both → train Isolation Forest on this combined "normal" corpus
  5. Save model to disk as pickle for fast reload

contamination:
  Set to 0.05 → expects ~5% of training data to be anomalous outliers.
  This is a safe conservative estimate.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .dataset_loader import load_cmapss, get_normal_data
from .feature_mapping import map_cmapss_to_twin, generate_twin_data

MODEL_DIR = Path(__file__).parent.parent / "data" / "models"
MODEL_PATH = MODEL_DIR / "isolation_forest.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"


def train_model(force_retrain: bool = False) -> tuple:
    """
    Train or load the Isolation Forest model.
    
    Steps:
    1. Load CMAPSS dataset (real or synthetic fallback)
    2. Extract early-cycle (normal) data
    3. Map to twin feature space
    4. Augment with simulated twin data
    5. Fit StandardScaler + IsolationForest
    6. Save both to disk

    Returns:
        (model, scaler) tuple
    """
    # Create model directory if needed
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if MODEL_PATH.exists() and SCALER_PATH.exists() and not force_retrain:
        print("[Model] Loading cached model from disk...")
        return load_model()

    print("[Model] === Starting ML Training Pipeline ===")

    # --- Step 1: Load CMAPSS dataset ---
    raw_df = load_cmapss("train_FD001.txt")

    # --- Step 2: Extract normal behavior (early cycles only) ---
    normal_cmapss = get_normal_data(raw_df, max_cycle=100)  # First 100 cycles = healthy

    # --- Step 3: Map CMAPSS features to twin error space ---
    cmapss_features = map_cmapss_to_twin(normal_cmapss)
    print(f"[Model] CMAPSS samples: {len(cmapss_features)}")

    # --- Step 4: Generate digital twin simulation data (augmentation) ---
    twin_features = generate_twin_data(n_samples=2000)
    # Remove injected fault samples from training — we only train on normal behavior
    # Normal = position_error < 0.3mm AND temperature_error < 3°C
    twin_normal = twin_features[
        (twin_features["position_error"] < 0.3) &
        (twin_features["temperature_error"] < 3.0)
    ]
    print(f"[Model] Twin simulation samples (normal only): {len(twin_normal)}")

    # --- Step 5: Combine and prepare feature matrix ---
    combined = pd.concat([cmapss_features, twin_normal], ignore_index=True)
    X = combined[["position_error", "temperature_error", "pwm_norm"]].values
    print(f"[Model] Total training samples: {len(X)}")

    # --- Step 6: Scale features ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- Step 7: Train Isolation Forest ---
    # contamination=0.05 means we expect up to 5% of training data to be outlier-like
    # n_estimators=200 for better stability
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        max_samples='auto',
        random_state=42,
        n_jobs=-1   # Use all CPU cores
    )
    model.fit(X_scaled)

    # --- Step 8: Save to disk ---
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    print(f"[Model] ✓ Model saved to {MODEL_PATH}")
    print(f"[Model] ✓ Scaler saved to {SCALER_PATH}")
    print("[Model] === Training Complete ===")

    return model, scaler


def load_model() -> tuple:
    """Load pre-trained model and scaler from disk."""
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    print("[Model] ✓ Loaded Isolation Forest from cache")
    return model, scaler
