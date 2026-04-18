"""
metadata.py — Model Metadata Persistence Helper

Saves and loads a metadata.json file alongside the .pkl model files.
Records: training timestamp, sample count, calibrated score range,
contamination setting, and validation metrics.

This solves:
  - Problem 6: No model metadata persistence
  - Problem 4: Score range needed for dynamic normalization in inference.py
  - Problem 7: Provides data for /ml/status API endpoint
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

METADATA_PATH = Path(__file__).parent.parent / "data" / "models" / "metadata.json"

_DEFAULT_METADATA: Dict[str, Any] = {
    "trained_at":    None,
    "n_samples":     0,
    "contamination": 0.05,
    "score_min":     -0.3,   # Conservative fallback (safe — won't crash inference)
    "score_max":      0.3,   # Conservative fallback
    "validation": {
        "normal_precision": None,
        "fault_recall":     None,
        "tested_at":        None,
    }
}


def save_metadata(
    n_samples:         int,
    score_min:         float,
    score_max:         float,
    contamination:     float = 0.05,
    validation:        Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Save model metadata to disk after training.
    Called by model.py immediately after model.fit().
    """
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "trained_at":    datetime.now(timezone.utc).isoformat(),
        "n_samples":     n_samples,
        "contamination": contamination,
        "score_min":     round(score_min, 6),
        "score_max":     round(score_max, 6),
        "validation":    validation or _DEFAULT_METADATA["validation"],
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[Metadata] Saved: score_min={score_min:.4f}, score_max={score_max:.4f}, n={n_samples}")
    return meta


def load_metadata() -> Dict[str, Any]:
    """
    Load model metadata from disk.
    Returns safe defaults if the file doesn't exist (first run or deleted).
    """
    if not METADATA_PATH.exists():
        print(f"[Metadata] metadata.json not found — using defaults (score range ±0.3)")
        return dict(_DEFAULT_METADATA)

    with open(METADATA_PATH, "r") as f:
        meta = json.load(f)

    print(f"[Metadata] Loaded: trained_at={meta.get('trained_at')}, n={meta.get('n_samples')}")
    return meta


def get_score_range() -> tuple[float, float]:
    """
    Convenience function: returns (score_min, score_max) for use in inference.
    Loads from disk on every call (cheap — tiny JSON file).
    """
    meta = load_metadata()
    return float(meta["score_min"]), float(meta["score_max"])
