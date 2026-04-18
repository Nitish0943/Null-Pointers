import asyncio
import httpx
import time
import random

API_URL = "http://localhost:8000/telemetry"

async def simulate_fault():
    print("[Start] Initiating Self-Healing Architecture Test...")
    print("[1] Sending 5 normal telemetry packets to establish baseline...")
    
    async with httpx.AsyncClient() as client:
        # 1. Baseline
        for _ in range(5):
            payload = {
                "position": 10.0 + random.uniform(-0.1, 0.1),
                "temperature": 25.0 + random.uniform(-0.5, 0.5),
                "pwm": 200,
                "steps": 1000
            }
            resp = await client.post(API_URL, json=payload)
            print(f"   [Nominal] Result: {resp.json().get('status')}")
            await asyncio.sleep(0.5)

        print("\n[2] INJECTING THERMAL RUNAWAY FAULT...")
        
        # 2. Inject fault (simulate a sudden huge spike in temperature)
        fault_payload = {
            "position": 10.0,
            "temperature": 85.5, # Critical overheat
            "pwm": 200,
            "steps": 1000
        }
        
        resp = await client.post(API_URL, json=fault_payload)
        data = resp.json()
        analysis = data.get("analysis", {})
        
        print("\n--- System Response ---")
        print(f"Risk Score:    {analysis.get('risk_score')}")
        print(f"Anomaly Flag:  {analysis.get('anomaly')}")
        
        # Check healing block
        healing = analysis.get("agents", {}).get("healing", {})
        if healing:
            print("\n--- Self-Healing Engine ---")
            print(f"Issue:           {healing.get('root_cause')}")
            print(f"Selected Action: {healing.get('selected_action')} (Value: {healing.get('action_value')})")
            print(f"Reasoning:       {healing.get('reasoning')}")
            print(f"Verification:    {healing.get('verification_status')}")
        else:
            print("\n[Failed] Self-healing engine did not trigger!")

        print("\n[3] Waiting 20 seconds for Background Recovery Monitor...")
        # Send recovered telemetry to simulate physics cooling down
        for i in range(10):
            await asyncio.sleep(2)
            cool_payload = {
                "position": 10.0,
                "temperature": 25.0 + i, # Back to normal cooling
                "pwm": 50, # PWM artificially lowered by healing!
                "steps": 1000
            }
            await client.post(API_URL, json=cool_payload)
            print(f"   [Recovery phase] Sent temp={cool_payload['temperature']}")

        print("\n✅ Test complete. Check the UI Dashboard to see the logs updated!")

if __name__ == "__main__":
    asyncio.run(simulate_fault())
