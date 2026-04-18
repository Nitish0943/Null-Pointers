"""
test_ml_pipeline.py — End-to-End ML Pipeline Validation

Tests each layer of the ML system:
  1. Dataset loading (CMAPSS / synthetic fallback)
  2. Feature mapping and augmentation
  3. Model training (Isolation Forest)
  4. Inference with known normal and anomaly inputs
  5. Live backend API integration test

Run from the backend directory:
    python test_ml_pipeline.py
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error

# Add backend to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
INFO = "ℹ️  INFO"

results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name))
    print(f"  {status}  {name}")
    if detail:
        print(f"           → {detail}")
    return condition


# ─────────────────────────────────────────────────
# TEST 1: Dataset Loader
# ─────────────────────────────────────────────────
print("\n" + "═"*60)
print("  TEST 1: Dataset Loader (CMAPSS / Synthetic Fallback)")
print("═"*60)

try:
    from app.ml.dataset_loader import load_cmapss, get_normal_data, preprocess

    raw = load_cmapss("train_FD001.txt")
    check("Dataset loaded (real or synthetic)", len(raw) > 0,
          f"{len(raw)} rows, columns: {list(raw.columns[:5])}...")

    normal = get_normal_data(raw, max_cycle=100)
    check("Normal data extraction (cycle ≤ 100)", len(normal) > 0,
          f"{len(normal)} normal samples extracted")

    check("Normalized columns in [0, 1]",
          all(normal[col].between(0, 1).all() for col in normal.columns),
          f"Columns: {list(normal.columns)}")

except Exception as e:
    check("Dataset loader import/run", False, str(e))


# ─────────────────────────────────────────────────
# TEST 2: Feature Mapping
# ─────────────────────────────────────────────────
print("\n" + "═"*60)
print("  TEST 2: Feature Mapping & Twin Data Generator")
print("═"*60)

try:
    from app.ml.feature_mapping import map_cmapss_to_twin, generate_twin_data, to_feature_vector
    import numpy as np

    # Map CMAPSS to twin space
    mapped = map_cmapss_to_twin(normal)
    check("CMAPSS → Twin mapping", list(mapped.columns) == ["position_error", "temperature_error", "pwm_norm"],
          f"Output columns: {list(mapped.columns)}")
    check("Position error in plausible range",
          mapped["position_error"].between(0, 1.5).all())
    check("Temperature error in plausible range",
          mapped["temperature_error"].between(0, 25).all())

    # Generate augmented twin data
    twin_data = generate_twin_data(n_samples=500)
    check("Twin simulation data generated", len(twin_data) == 500,
          f"{len(twin_data)} samples")

    # Feature vector converter
    vec = to_feature_vector(0.1, 2.5, 150)
    check("Feature vector shape (1, 3)", vec.shape == (1, 3),
          f"Shape: {vec.shape}, Values: {vec}")

except Exception as e:
    check("Feature mapping import/run", False, str(e))


# ─────────────────────────────────────────────────
# TEST 3: Model Training
# ─────────────────────────────────────────────────
print("\n" + "═"*60)
print("  TEST 3: Isolation Forest Training & Persistence")
print("═"*60)

try:
    from app.ml.model import train_model, MODEL_PATH, SCALER_PATH

    print(f"  {INFO}  Training model (first-run may take a few seconds)...")
    t0 = time.time()
    model, scaler = train_model(force_retrain=True)
    elapsed = time.time() - t0

    check("Model trained successfully", model is not None,
          f"Completed in {elapsed:.2f}s")
    check("Scaler fitted successfully", scaler is not None)
    check("Model file saved to disk", MODEL_PATH.exists(),
          str(MODEL_PATH))
    check("Scaler file saved to disk", SCALER_PATH.exists(),
          str(SCALER_PATH))

    # Verify model has the expected API
    check("Model has predict() method",   hasattr(model, 'predict'))
    check("Model has decision_function()", hasattr(model, 'decision_function'))

except Exception as e:
    check("Model training", False, str(e))


# ─────────────────────────────────────────────────
# TEST 4: Inference — Normal Cases
# ─────────────────────────────────────────────────
print("\n" + "═"*60)
print("  TEST 4: Inference — Normal Telemetry")
print("═"*60)

NORMAL_CASES = [
    {"name": "Idle (zero error)",      "pos": 0.01, "temp": 0.5,  "pwm": 100},
    {"name": "Light load",             "pos": 0.05, "temp": 1.2,  "pwm": 150},
    {"name": "Moderate operation",     "pos": 0.10, "temp": 2.0,  "pwm": 180},
    {"name": "Near threshold (safe)",  "pos": 0.25, "temp": 4.0,  "pwm": 200},
]

try:
    from app.ml.inference import predict_anomaly

    for case in NORMAL_CASES:
        result = predict_anomaly(case["pos"], case["temp"], case["pwm"])
        is_safe = result["risk_score"] < 0.6
        check(
            f"Normal: {case['name']}",
            is_safe,
            f"risk={result['risk_score']:.3f}  anomaly={result['anomaly']}  "
            f"score={result['anomaly_score']:.3f}  → {result['recommendation'][:50]}"
        )

except Exception as e:
    check("Normal inference", False, str(e))


# ─────────────────────────────────────────────────
# TEST 5: Inference — Anomaly Cases
# ─────────────────────────────────────────────────
print("\n" + "═"*60)
print("  TEST 5: Inference — Fault / Anomaly Telemetry")
print("═"*60)

ANOMALY_CASES = [
    {"name": "Thermal runaway",        "pos": 0.05, "temp": 20.0, "pwm": 200},
    {"name": "Motor position drift",   "pos": 1.2,  "temp": 1.0,  "pwm": 200},
    {"name": "Combined fault",         "pos": 1.0,  "temp": 18.0, "pwm": 255},
    {"name": "Severe overheat",        "pos": 0.02, "temp": 25.0, "pwm": 100},
]

try:
    for case in ANOMALY_CASES:
        result = predict_anomaly(case["pos"], case["temp"], case["pwm"])
        is_flagged = result["risk_score"] > 0.4 or result["issue_detected"]
        check(
            f"Anomaly: {case['name']}",
            is_flagged,
            f"risk={result['risk_score']:.3f}  anomaly={result['anomaly']}  "
            f"score={result['anomaly_score']:.3f}  → {result['recommendation'][:60]}"
        )

except Exception as e:
    check("Anomaly inference", False, str(e))


# ─────────────────────────────────────────────────
# TEST 6: Live API Integration
# ─────────────────────────────────────────────────
print("\n" + "═"*60)
print("  TEST 6: Live Backend API Integration (http://localhost:8000)")
print("═"*60)

BASE_URL = "http://localhost:8000"

def api_get(path):
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception as e:
        return None, str(e)

def api_post(path, data):
    try:
        payload = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{BASE_URL}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": body}, e.code
    except Exception as e:
        return None, str(e)

# Health check
resp, status = api_get("/")
check("GET / — Backend online", status == 200, f"Response: {resp}")

# Post normal telemetry
telemetry_normal = {"position": 10.05, "temperature": 28.5, "pwm": 150, "steps": 200}
resp, status = api_post("/telemetry", telemetry_normal)
check("POST /telemetry — Normal sample accepted", status == 200,
      f"Status={status}  Response keys: {list(resp.keys()) if resp else 'none'}")

# Check if ML fields are in response
if resp and "analysis" in str(resp):
    print(f"           → Analysis: {resp}")

# Post anomaly telemetry
telemetry_fault = {"position": 10.5, "temperature": 65.0, "pwm": 250, "steps": 200}
resp_fault, status_fault = api_post("/telemetry", telemetry_fault)
check("POST /telemetry — Fault sample accepted", status_fault == 200,
      f"Status={status_fault}")

# Analytics endpoint
resp_a, status_a = api_get("/analytics")
check("GET /analytics — Returns ML results", status_a == 200,
      f"risk_score={resp_a.get('risk_score') if resp_a else 'N/A'}"
      f"  anomaly={resp_a.get('anomaly') if resp_a else 'N/A'}"
      f"  issue={resp_a.get('issue_detected') if resp_a else 'N/A'}")

if resp_a:
    check("Analytics includes anomaly_score field", "anomaly_score" in resp_a,
          f"anomaly_score={resp_a.get('anomaly_score')}")
    check("Analytics includes recommendation field", "recommendation" in resp_a,
          f"→ {str(resp_a.get('recommendation', ''))[:70]}")

# History endpoint
resp_h, status_h = api_get("/history?limit=5")
check("GET /history — Returns telemetry records", status_h == 200,
      f"{len(resp_h) if isinstance(resp_h, list) else 0} records returned")


# ─────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────
passed = sum(1 for s, _ in results if s == PASS)
total  = len(results)
failed = [name for s, name in results if s == FAIL]

print("\n" + "═"*60)
print(f"  RESULTS:  {passed}/{total} tests passed")
print("═"*60)

if failed:
    print("\n  Failed tests:")
    for name in failed:
        print(f"    {FAIL}  {name}")
else:
    print("\n  🎉  All tests passed! ML pipeline is fully operational.")

print()
