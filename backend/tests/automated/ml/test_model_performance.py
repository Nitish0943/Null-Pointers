import pytest
import numpy as np
from app.ml.inference import anomaly_detector
from .generate_synthetic_data import generate_test_batch

def test_anomaly_detection_accuracy():
    # 1. Normal State
    normal_data = generate_test_batch("normal", 20)
    anomalies_found = 0
    for _, row in normal_data.iterrows():
        res = anomaly_detector.predict(row.to_dict())
        if res['anomaly']: anomalies_found += 1
    
    # FPR should be reasonably low
    fpr = anomalies_found / 20
    assert fpr <= 0.15, f"False Positive Rate too high: {fpr}"

def test_overheating_detection():
    # 2. Overheating State
    faulty_data = generate_test_batch("overheating", 20)
    # The latter half should be detected as anomalous
    detections = 0
    for i, row in faulty_data.iterrows():
        res = anomaly_detector.predict(row.to_dict())
        if res['anomaly']: detections += 1
    
    recall = detections / 20
    assert recall >= 0.7, f"Overheating detection recall too low: {recall}"

def test_inference_latency():
    # Verify processing speed
    import time
    sample = {"actual_position": 50, "actual_temperature": 40, "position_error": 0, "temperature_error": 0}
    
    start = time.time()
    for _ in range(100):
        anomaly_detector.predict(sample)
    duration = (time.time() - start) / 100
    
    assert duration < 0.05, f"Inference too slow: {duration:.4f}s"
