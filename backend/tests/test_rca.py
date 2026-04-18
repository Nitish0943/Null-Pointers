"""
test_rca.py — Root Cause Analysis Engine Integration Test
Run from backend/ directory: python test_rca.py
"""
import sys, os, json, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

PASS = "PASS"
FAIL = "FAIL"

def post(url, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload,
          headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:
        return 0, {"error": str(e)}

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return 0, {"error": str(e)}

BASE = "http://localhost:8000"
results = []

def check(label, cond, detail=""):
    status = PASS if cond else FAIL
    results.append((status, label))
    print(f"  [{status}] {label}")
    if detail:
        print(f"         > {detail}")

# ─── UNIT TEST: RCA Engine directly ──────────────────────────────────────────
print("\n=== UNIT: RCA Engine Direct Tests ===")
from app.services.rca_engine import RCAEngine

eng = RCAEngine()

# Warm up with some normal readings first
for i in range(12):
    eng.analyze(
        actual={"position": 10.0+i*0.05, "temperature": 30.0+i*0.1, "current": 1.2},
        predicted={"position": 10.0+i*0.05, "temperature": 30.0+i*0.1},
        pos_error=0.02, temp_error=0.5, anomaly_score=0.1, pwm=120
    )

# Test 1: Normal — no fault
r = eng.analyze(
    actual={"position": 10.5, "temperature": 31.0, "current": 1.3},
    predicted={"position": 10.5, "temperature": 31.2},
    pos_error=0.02, temp_error=0.5, anomaly_score=0.08, pwm=120
)
check("Normal: root_cause = 'No Fault Detected'",
      r["root_cause"] == "No Fault Detected",
      f"got: {r['root_cause']}  confidence={r['confidence_score']}")

# Test 2: Mechanical Jam
r = eng.analyze(
    actual={"position": 10.5, "temperature": 32.0, "current": 4.8},
    predicted={"position": 11.2, "temperature": 32.0},
    pos_error=0.95, temp_error=0.5, anomaly_score=0.75, pwm=200
)
check("Fault: Mechanical Jam detected",
      "Mechanical" in r["root_cause"] or "Jam" in r["root_cause"],
      f"root_cause={r['root_cause']}  confidence={r['confidence_score']}  severity={r['severity']}")
check("Mechanical Jam: reasoning list populated",
      len(r.get("reasoning", [])) >= 2,
      f"reasoning: {r.get('reasoning')}")

# Test 3: Thermal Runaway
r = eng.analyze(
    actual={"position": 10.5, "temperature": 110.0, "current": 1.1},
    predicted={"position": 10.5, "temperature": 40.0},
    pos_error=0.02, temp_error=70.0, anomaly_score=0.92, pwm=80
)
check("Fault: Thermal Runaway detected",
      "Thermal" in r["root_cause"] or "Runaway" in r["root_cause"],
      f"root_cause={r['root_cause']}  severity={r['severity']}")
check("Thermal Runaway: severity is CRITICAL or HIGH",
      r["severity"] in ("CRITICAL", "HIGH"),
      f"severity={r['severity']}")

# Test 4: Motor Step Loss
r = eng.analyze(
    actual={"position": 13.0, "temperature": 31.0, "current": 0.9},
    predicted={"position": 10.5, "temperature": 31.0},
    pos_error=2.5, temp_error=0.3, anomaly_score=0.55, pwm=100
)
check("Fault: Motor Step Loss detected",
      "Step" in r["root_cause"] or "Calibration" in r["root_cause"] or "Motor" in r["root_cause"],
      f"root_cause={r['root_cause']}  confidence={r['confidence_score']}")

# Test 5: Confidence score range
check("Confidence score in [0, 1]",
      0.0 <= r["confidence_score"] <= 1.0,
      f"confidence={r['confidence_score']}")

# Test 6: derived_features present
check("Derived features returned",
      "derived_features" in r and len(r["derived_features"]) > 5,
      f"features: {list(r.get('derived_features', {}).keys())}")

# ─── INTEGRATION: Live API Tests ──────────────────────────────────────────────
print("\n=== INTEGRATION: Live API Tests ===")

# Normal telemetry
print("\nCase A: Normal telemetry → /telemetry")
s, resp = post(f"{BASE}/telemetry", {"position": 10.5, "temperature": 32.0, "pwm": 120, "steps": 210})
check("POST /telemetry 200 OK", s == 200, f"status={s}")

# Fault injection via ESP32 endpoint
print("\nCase B: Thermal fault via /esp32/telemetry (temp=95, current=4.8)")
s, resp = post(f"{BASE}/esp32/telemetry",
               {"tilt": 45.0, "temperature": 95.0, "current": 4.8})
check("POST /esp32/telemetry 200 OK", s == 200, f"status={s}")
if s == 200:
    a = resp.get("analysis", {})
    rca = a.get("rca", {})
    check("ESP32 response includes RCA block", bool(rca), f"rca keys: {list(rca.keys())}")
    check("RCA root_cause is string", isinstance(rca.get("root_cause"), str),
          f"root_cause={rca.get('root_cause')}")
    check("RCA severity present", "severity" in rca, f"severity={rca.get('severity')}")
    check("RCA reasoning is list", isinstance(rca.get("reasoning", []), list),
          f"reasoning count={len(rca.get('reasoning', []))}")
    print(f"\n         RCA Result:")
    print(f"           root_cause : {rca.get('root_cause')}")
    print(f"           confidence : {rca.get('confidence_score')}")
    print(f"           severity   : {rca.get('severity')}")
    print(f"           action     : {str(rca.get('recommended_action',''))[:80]}")

# Analytics endpoint includes RCA
print("\nCase C: GET /analytics includes RCA fields")
s, resp = get(f"{BASE}/analytics")
check("GET /analytics 200 OK", s == 200, f"status={s}")
if s == 200:
    rca = resp.get("rca", {})
    check("Analytics response has rca block", bool(rca), f"keys: {list(resp.keys())}")
    check("Analytics rca.root_cause present", "root_cause" in rca,
          f"root_cause={rca.get('root_cause')}")
    check("Analytics rca.severity present", "severity" in rca)
    check("Analytics rca.reasoning is list",
          isinstance(rca.get("reasoning", []), list))

# Summary
passed = sum(1 for s, _ in results if s == PASS)
total = len(results)
failed = [(n, s) for s, n in results if s == FAIL]

print(f"\n{'='*55}")
print(f"  RESULTS: {passed}/{total} passed")
print(f"{'='*55}")
if failed:
    print("\n  Failed:")
    for n, _ in failed:
        print(f"  [FAIL] {n}")
else:
    print("  All tests passed! RCA Engine is fully operational.")
print()
