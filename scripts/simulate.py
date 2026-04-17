import requests
import time
import random

API_URL = "http://localhost:8000/telemetry"

def simulate():
    print("🚀 Starting Digital Twin Simulation...")
    current_steps = 0
    current_temp = 25.0
    
    for i in range(100):
        # Simulate Physical Perturbations
        pwm = 150 if i < 50 else 50
        steps_inc = 10
        current_steps += steps_inc
        
        # Add some noise to "Actual" data to simulate hardware
        actual_pos = current_steps * 0.05 + random.uniform(-0.02, 0.02)
        actual_temp = current_temp + (pwm/255.0)*0.2 - 0.05 + random.uniform(-0.1, 0.1)
        current_temp = actual_temp
        
        # Occasional Anomaly (Simulate friction/overheat)
        if i == 75:
            actual_temp += 10.0
            print("⚠ Injecting Anomaly: Sudden temperature spike!")

        payload = {
            "position": actual_pos,
            "temperature": actual_temp,
            "pwm": pwm,
            "steps": current_steps
        }
        
        try:
            response = requests.post(API_URL, json=payload)
            print(f"[{i:02}] Data Sent | Pos: {actual_pos:.2f} | Temp: {actual_temp:.1f} | Result: {response.json()['analysis']['recommendation']}")
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    simulate()
