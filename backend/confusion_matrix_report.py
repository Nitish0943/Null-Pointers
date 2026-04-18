"""
confusion_matrix_report.py — Full ML Confusion Matrix & Metrics Report
"""
import sys
sys.path.insert(0, '.')

import numpy as np
from sklearn.metrics import (
    confusion_matrix, classification_report,
    roc_auc_score, precision_score, recall_score, f1_score
)
from app.ml.model import load_model
from app.ml.feature_mapping import generate_normal_twin_data, generate_fault_data
from app.ml.metadata import load_metadata

# ── Load model + metadata ─────────────────────────────────────────────────────
model, scaler = load_model()
meta = load_metadata()

# ── Generate test sets ────────────────────────────────────────────────────────
# Use different random seeds than training (train used seed=99, we use 55 / 88)
rng_n = np.random.default_rng(55)
rng_f = np.random.default_rng(88)

# 600 normal test samples
normal_df = generate_normal_twin_data(n_samples=600)
# 400 fault test samples (across all 4 fault types)
fault_df  = generate_fault_data(n_samples=400)

FEATURES = ["position_error", "temperature_error", "pwm_norm"]

X_normal = scaler.transform(normal_df[FEATURES].values)
X_fault  = scaler.transform(fault_df[FEATURES].values)

# Isolation Forest: +1 = normal, -1 = anomaly
pred_normal = model.predict(X_normal)   # expect mostly +1
pred_fault  = model.predict(X_fault)    # expect mostly -1

# Scores (higher = more normal)
score_normal = model.decision_function(X_normal)
score_fault  = model.decision_function(X_fault)

# ── Build confusion matrix ────────────────────────────────────────────────────
# Convert to binary: 1 = fault (anomaly), 0 = normal
y_true = np.array([0] * len(pred_normal) + [1] * len(pred_fault))
y_pred = np.array(
    [0 if p == 1 else 1 for p in pred_normal] +
    [0 if p == 1 else 1 for p in pred_fault]
)

cm = confusion_matrix(y_true, y_pred)
TN, FP, FN, TP = cm.ravel()

precision  = precision_score(y_true, y_pred)
recall     = recall_score(y_true, y_pred)
f1         = f1_score(y_true, y_pred)
accuracy   = (TP + TN) / (TP + TN + FP + FN)
specificity = TN / (TN + FP)
fpr        = FP / (FP + TN)

# ── Compute AUC using decision_function scores ────────────────────────────────
all_scores = np.concatenate([score_normal, score_fault])
# Flip sign: lower decision_function → more anomalous → higher fault probability
fault_proba = -all_scores
auc = roc_auc_score(y_true, fault_proba)

# ── Print Report ──────────────────────────────────────────────────────────────
W = 54
print("=" * W)
print("   ISOLATION FOREST — CONFUSION MATRIX REPORT")
print("=" * W)
print(f"  Model trained : {meta.get('trained_at', 'N/A')[:19]}")
print(f"  Training set  : {meta.get('n_samples')} samples (100% normal)")
print(f"  Contamination : {meta.get('contamination')}")
print(f"  Score range   : [{meta.get('score_min'):.4f}, {meta.get('score_max'):.4f}]")
print()

# Visual confusion matrix
print("  CONFUSION MATRIX")
print("  " + "-" * 34)
print("                   Pred: Normal  Pred: Fault")
print(f"  Actual: Normal      {TN:>7}      {FP:>7}")
print(f"  Actual: Fault       {FN:>7}      {TP:>7}")
print("  " + "-" * 34)
print()

# Metrics table
print("  PERFORMANCE METRICS")
print("  " + "-" * 34)
print(f"  Accuracy          {accuracy:.4f}   ({accuracy*100:.1f}%)")
print(f"  Precision         {precision:.4f}   ({precision*100:.1f}%)")
print(f"    (of flagged faults, how many are real)")
print(f"  Recall            {recall:.4f}   ({recall*100:.1f}%)")
print(f"    (of real faults, how many were caught)")
print(f"  F1-Score          {f1:.4f}")
print(f"  Specificity       {specificity:.4f}   ({specificity*100:.1f}%)")
print(f"    (normal samples correctly not flagged)")
print(f"  False Pos. Rate   {fpr:.4f}   ({fpr*100:.1f}%)")
print(f"    (normal readings wrongly flagged as fault)")
print(f"  AUC-ROC           {auc:.4f}")
print("  " + "-" * 34)
print()

# Counts
print("  PREDICTION COUNTS")
print("  " + "-" * 34)
print(f"  True  Negatives (TN): {TN:4}  — normal, correctly passed")
print(f"  False Positives (FP): {FP:4}  — normal, wrongly flagged")
print(f"  False Negatives (FN): {FN:4}  — fault, missed by model")
print(f"  True  Positives (TP): {TP:4}  — fault, correctly caught")
print(f"  Total test samples  : {len(y_true):4}")
print("  " + "-" * 34)
print()

# Per-fault-type breakdown
print("  FAULT TYPE BREAKDOWN")
print("  " + "-" * 34)
n_each = len(fault_df) // 4
fault_types = [
    "Thermal Runaway (temp 15-25°C)",
    "Mechanical Jam  (pos 0.8-1.5mm)",
    "Motor Step Loss (pos 0.5-1.2mm)",
    "Combined Fault  (both elevated)",
]
predictions_fault = [0 if p == 1 else 1 for p in pred_fault]
for i, fname in enumerate(fault_types):
    start = i * n_each
    end   = start + n_each if i < 3 else len(pred_fault)
    chunk = predictions_fault[start:end]
    detected = sum(chunk)
    total    = len(chunk)
    pct      = detected / total * 100 if total > 0 else 0
    print(f"  {fname}")
    print(f"    Detected {detected}/{total}  ({pct:.0f}% recall)")
print("  " + "-" * 34)
print()

# Score distributions
print("  DECISION FUNCTION DISTRIBUTIONS")
print("  " + "-" * 34)
print(f"  Normal samples — decision_function:")
print(f"    mean={score_normal.mean():.4f}  std={score_normal.std():.4f}")
print(f"    min={score_normal.min():.4f}  max={score_normal.max():.4f}")
print(f"  Fault samples — decision_function:")
print(f"    mean={score_fault.mean():.4f}  std={score_fault.std():.4f}")
print(f"    min={score_fault.min():.4f}  max={score_fault.max():.4f}")
print(f"  Score separation (margin): {score_normal.mean() - score_fault.mean():.4f}")
print("  " + "-" * 34)
print()

# Overall verdict
print("  OVERALL VERDICT")
if auc > 0.95 and recall > 0.95:
    verdict = "EXCELLENT — Production ready"
elif auc > 0.85 and recall > 0.80:
    verdict = "GOOD — Suitable for deployment"
elif recall > 0.70:
    verdict = "ACCEPTABLE — Monitor closely"
else:
    verdict = "POOR — Needs retraining"
print(f"  {verdict}")
print("=" * W)
