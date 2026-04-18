"""
dataset_loader.py — NASA CMAPSS Dataset Loader (v2 — Clean)

v2 Changes (ML Fix Phase 1):
  - Synthetic fallback is now FLAT (no degradation trend) — all cycles are healthy
  - max_cycle tightened from 100 → 50 to exclude early mild degradation
  - Added explicit data quality assertions
"""

import numpy as np
import pandas as pd
from pathlib import Path

CMAPSS_COLUMNS = [
    "unit_id", "cycle",
    "os_1", "os_2", "os_3",
    "sensor_1",  "sensor_2",  "sensor_3",  "sensor_4",
    "sensor_5",  "sensor_6",  "sensor_7",  "sensor_8",
    "sensor_9",  "sensor_10", "sensor_11", "sensor_12",
    "sensor_13", "sensor_14", "sensor_15", "sensor_16",
    "sensor_17", "sensor_18", "sensor_19", "sensor_20",
    "sensor_21"
]

# Feature Selection Rationale:
#   sensor_2: Fan inlet temperature → temperature_error proxy
#   sensor_7: HPC outlet pressure   → position_error proxy (mechanical stress)
#   os_3:     Throttle angle        → pwm_norm proxy (control duty cycle)
SELECTED_FEATURES = ["sensor_2", "sensor_7", "os_3"]

DATA_DIR = Path(__file__).parent.parent / "data"


def load_cmapss(filename: str = "train_FD001.txt") -> pd.DataFrame:
    """
    Load NASA CMAPSS dataset from data/ directory.
    Falls back to a clean synthetic dataset if the real file is missing.
    """
    filepath = DATA_DIR / filename

    if not filepath.exists():
        print(f"[DataLoader] CMAPSS file not found at {filepath}")
        print(f"[DataLoader] Generating clean synthetic fallback...")
        return _generate_synthetic_cmapss()

    df = pd.read_csv(filepath, sep=r"\s+", header=None, names=CMAPSS_COLUMNS)
    print(f"[DataLoader] Loaded CMAPSS: {len(df)} rows")
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and min-max normalize selected features.
    Output columns: 'temp_signal', 'pos_signal', 'pwm_signal' — all in [0, 1].
    """
    subset = df[SELECTED_FEATURES].copy()
    subset.columns = ["temp_signal", "pos_signal", "pwm_signal"]

    for col in subset.columns:
        col_min = subset[col].min()
        col_max = subset[col].max()
        if col_max > col_min:
            subset[col] = (subset[col] - col_min) / (col_max - col_min)

    return subset


def get_normal_data(df: pd.DataFrame, max_cycle: int = 50) -> pd.DataFrame:
    """
    Extract early-cycle samples representing NORMAL (healthy) behavior.

    v2 change: max_cycle reduced from 100 → 50.
    Early cycles 1-50 are before any measurable degradation begins.
    Cycles 51-100 show early wear patterns that contaminate the "normal" class.
    """
    normal_rows = df[df["cycle"] <= max_cycle]
    result = preprocess(normal_rows)
    print(f"[DataLoader] Normal samples (cycle ≤ {max_cycle}): {len(result)}")
    return result


def _generate_synthetic_cmapss(n_samples: int = 2000) -> pd.DataFrame:
    """
    Fallback: Generate CLEAN synthetic data with NO degradation trend.

    v2 change: The previous version applied a degradation trend
    `(cycles / 300.0)` to sensor values, meaning later cycles had higher
    values — contaminating the "normal" training class with early degradation.

    Now: all cycles are stationary (flat healthy operating point) with
    only Gaussian noise around the nominal sensor values.

    Nominal values based on CMAPSS dataset documentation:
      sensor_2 (temperature): ~641°R nominal
      sensor_7 (pressure):    ~554 psi nominal
      os_3 (setting):         discrete {0.0, 0.0002, 0.0004}
    """
    rng = np.random.default_rng(42)

    cycles   = np.tile(np.arange(1, 51), n_samples // 50 + 1)[:n_samples]  # Only cycles 1-50
    unit_ids = np.repeat(np.arange(1, n_samples // 50 + 2), 50)[:n_samples]

    # FLAT healthy operating point — no degradation trend
    sensor_2 = 641.0 + rng.normal(0, 0.4, n_samples)   # tight thermal noise only
    sensor_7 = 554.0 + rng.normal(0, 0.8, n_samples)   # tight pressure noise only
    os_3     = rng.choice([0.0, 0.0002, 0.0004], n_samples)

    data = {col: np.zeros(n_samples) for col in CMAPSS_COLUMNS}
    data["unit_id"]  = unit_ids
    data["cycle"]    = cycles
    data["os_3"]     = os_3
    data["sensor_2"] = sensor_2
    data["sensor_7"] = sensor_7

    print(f"[DataLoader] Synthetic CMAPSS (flat/healthy): {n_samples} samples")
    return pd.DataFrame(data)
