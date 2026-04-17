import json
import urllib.request
import urllib.error

BASE = 'http://localhost:8000'

def post(path, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        f'{BASE}{path}', data=payload,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:
        return 0, {"error": str(e)}

print("=" * 55)
print("  ESP32 Endpoint Integration Tests")
print("=" * 55)

# Test 1: Old payload to old endpoint — expect 422
print("\nTEST 1: Old payload to /telemetry  (expected 422)")
s, r = post('/telemetry', {'tilt': 12.4, 'temperature': 38.5, 'current': 1.2})
print(f"  Status : {s}")
if s == 422:
    print("  PASS   : 422 Unprocessable Entity as expected")
else:
    print(f"  RESULT : {r}")

# Test 2: Correct ESP32 payload to new endpoint — expect 200
print("\nTEST 2: ESP32 payload to /esp32/telemetry  (expected 200)")
s, r = post('/esp32/telemetry', {'tilt': 12.4, 'temperature': 38.5, 'current': 1.2})
print(f"  Status       : {s}")
print(f"  Source       : {r.get('source')}")
print(f"  Mapped       : {r.get('mapped')}")
a = r.get('analysis', {})
print(f"  risk_score   : {a.get('risk_score')}")
print(f"  anomaly      : {a.get('anomaly')}")
print(f"  Recommend    : {str(a.get('recommendation',''))[:70]}")
if s == 200:
    print("  PASS   : 200 OK")
else:
    print(f"  FAIL   : {r}")

# Test 3: Missing required field — expect 422
print("\nTEST 3: Missing 'current' field  (expected 422)")
s, r = post('/esp32/telemetry', {'tilt': 5.0, 'temperature': 30.0})
print(f"  Status : {s}")
if s == 422:
    missing = r.get('detail', [{}])
    if isinstance(missing, list):
        print(f"  Field  : {missing[0].get('loc')}")
    print("  PASS   : Validation rejected missing field correctly")
else:
    print(f"  RESULT : {r}")

# Test 4: Fault injection — high temp
print("\nTEST 4: Fault injection (tilt=45, temp=95, current=4.5)")
s, r = post('/esp32/telemetry', {'tilt': 45.0, 'temperature': 95.0, 'current': 4.5})
print(f"  Status       : {s}")
a = r.get('analysis', {})
print(f"  risk_score   : {a.get('risk_score')}")
print(f"  anomaly      : {a.get('anomaly')}")
print(f"  issue_detect : {a.get('issue_detected')}")
print(f"  Recommend    : {str(a.get('recommendation',''))[:80]}")

print("\n" + "=" * 55)
