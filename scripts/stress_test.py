import requests
import time
import random

API_URL = "http://localhost:8000/telemetry"

def run_stress_test(events=1000, delay=0.01):
    print(f"Starting Stress Test: {events} events with {delay}s delay...")
    success = 0
    failures = 0
    
    start_time = time.time()
    
    for i in range(events):
        payload = {
            "timestamp": int(time.time()),
            "actual_position": 50 + random.uniform(-2, 2),
            "actual_temperature": 40 + random.uniform(-5, 5),
            "pwm": 128,
            "steps": 1000 + i,
            "source": "stress_node"
        }
        
        try:
            resp = requests.post(API_URL, json=payload, timeout=1)
            if resp.status_code == 200:
                success += 1
            else:
                failures += 1
        except Exception:
            failures += 1
            
        if i % 100 == 0:
            print(f"Progress: {i}/{events} events sent...")

    total_time = time.time() - start_time
    print(f"\n--- Stress Test Completed ---")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Success: {success}")
    print(f"Failures: {failures}")
    print(f"Throughput: {success/total_time:.2f} req/s")

if __name__ == "__main__":
    run_stress_test(500, 0.02)
