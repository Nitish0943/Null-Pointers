import sys, os
sys.path.insert(0, '.')

from app.ml.model import train_model
from app.ml.metadata import load_metadata

print("=== Training with fixed clean data ===")
model, scaler = train_model(force_retrain=True)

print()
print("=== Model Metadata ===")
meta = load_metadata()
for k, v in meta.items():
    print(f"  {k}: {v}")

print()
print("=== Inference Sanity Check ===")
from app.ml.inference import predict_anomaly

# Normal reading
r = predict_anomaly(0.05, 0.4, 120)
print(f"  Normal:  risk={r['risk_score']}  anomaly={r['anomaly']}  score={r['anomaly_score']}")

# Clear fault
r = predict_anomaly(1.2, 18.0, 200)
print(f"  Fault:   risk={r['risk_score']}  anomaly={r['anomaly']}  score={r['anomaly_score']}")

# Borderline
r = predict_anomaly(0.35, 5.0, 150)
print(f"  Border:  risk={r['risk_score']}  anomaly={r['anomaly']}  score={r['anomaly_score']}")

print()
print("=== Validation Summary ===")
val = meta.get("validation", {})
print(f"  normal_precision : {val.get('normal_precision')}")
print(f"  fault_recall     : {val.get('fault_recall')}")
print(f"  score_min        : {meta.get('score_min')}")
print(f"  score_max        : {meta.get('score_max')}")
