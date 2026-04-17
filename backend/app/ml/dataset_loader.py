"""
dataset_loader.py — NASA CMAPSS Dataset Loader

The NASA CMAPSS (Commercial Modular Aero-Propulsion System Simulation) dataset
contains run-to-failure telemetry of turbofan engines. Although it's aerospace data,
the underlying physics (thermal degradation, mechanical drift) are analogous to
our motor-heater subsystem. We extract the relevant signals and map them to
our domain.

Dataset URL: https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/
File: CMAPSSData.zip → train_FD001.txt
"""

import os
import io
import numpy as np
import pandas as pd
from pathlib import Path

# Column names for CMAPSS dataset (as defined in the NASA documentation)
CMAPSS_COLUMNS = [
    "unit_id", "cycle",
    "os_1", "os_2", "os_3",                            # Operational Settings
    "sensor_1",  "sensor_2",  "sensor_3",  "sensor_4",  # Sensor readings
    "sensor_5",  "sensor_6",  "sensor_7",  "sensor_8",
    "sensor_9",  "sensor_10", "sensor_11", "sensor_12",
    "sensor_13", "sensor_14", "sensor_15", "sensor_16",
    "sensor_17", "sensor_18", "sensor_19", "sensor_20",
    "sensor_21"
]

# --- Feature Selection Rationale ---
# sensor_2:  Fan inlet temperature — mirrors our heater temperature signal
#            (rises as the system heats up / degrades)
# sensor_7:  HPC outlet pressure   — mirrors mechanical load / position error
#            (increases under stress, analogous to motor resistance/drift)
# os_3:      Throttle resolver angle / operating regime — mirrors PWM control duty
#
SELECTED_FEATURES = ["sensor_2", "sensor_7", "os_3"]

DATA_DIR = Path(__file__).parent.parent / "data"


def load_cmapss(filename: str = "train_FD001.txt") -> pd.DataFrame:
    """
    Load NASA CMAPSS dataset from the data/ directory.
    If file is not found, a synthetic fallback is generated (for development).
    """
    filepath = DATA_DIR / filename

    if not filepath.exists():
        print(f"[DataLoader] ⚠ CMAPSS file not found at {filepath}")
        print(f"[DataLoader] Generating synthetic fallback dataset...")
        return _generate_synthetic_cmapss()

    df = pd.read_csv(filepath, sep=r"\s+", header=None, names=CMAPSS_COLUMNS)
    print(f"[DataLoader] ✓ Loaded CMAPSS: {len(df)} rows, {len(df.columns)} columns")
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and normalize selected features for ML training.
    Returns a dataframe with 3 columns mapped to our system's domain.
    """
    subset = df[SELECTED_FEATURES].copy()

    # Rename to match our domain language
    subset.columns = ["temp_signal", "pos_signal", "pwm_signal"]

    # Normalize each column to 0-1 (min-max scaling)
    for col in subset.columns:
        col_min = subset[col].min()
        col_max = subset[col].max()
        if col_max > col_min:
            subset[col] = (subset[col] - col_min) / (col_max - col_min)

    return subset


def get_normal_data(df: pd.DataFrame, max_cycle: int = 100) -> pd.DataFrame:
    """
    Extract samples from early cycles (cycle <= max_cycle).
    These represent NORMAL behavior before any degradation occurs.
    This is the training set for the Isolation Forest.
    """
    normal_rows = df[df["cycle"] <= max_cycle]
    return preprocess(normal_rows)


def _generate_synthetic_cmapss(n_samples: int = 3000) -> pd.DataFrame:
    """
    Fallback: Generate synthetic data that mimics CMAPSS behavior.
    Used when the real dataset is not downloaded.
    
    - sensor_2 (temp): Normal operating range ≈ 641-650
    - sensor_7 (pressure): Normal operating range ≈ 554-568
    - os_3 (setting): Categorical {-0.0006, 0.0002, ...}
    - cycle: 1 to 300
    """
    rng = np.random.default_rng(42)

    cycles = np.tile(np.arange(1, 301), n_samples // 300 + 1)[:n_samples]
    unit_ids = np.repeat(np.arange(1, n_samples // 300 + 2), 300)[:n_samples]

    # Simulate normal behavior with slight degradation trend
    degradation = cycles / 300.0  # 0 to ~1
    sensor_2 = 641 + 9 * degradation + rng.normal(0, 0.5, n_samples)
    sensor_7 = 554 + 14 * degradation + rng.normal(0, 1.0, n_samples)
    os_3 = rng.choice([0.0, 0.0002, 0.0004], n_samples)

    data = {col: np.zeros(n_samples) for col in CMAPSS_COLUMNS}
    data["unit_id"] = unit_ids
    data["cycle"] = cycles
    data["os_3"] = os_3
    data["sensor_2"] = sensor_2
    data["sensor_7"] = sensor_7

    print(f"[DataLoader] ✓ Synthetic CMAPSS: {n_samples} samples generated")
    return pd.DataFrame(data)
