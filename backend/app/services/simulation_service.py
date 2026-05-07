import asyncio
import random
import time
from .ingestion_service import ingestion_service
from ..db.database import SessionLocal

class SimulationEngine:
    def __init__(self):
        self.is_running = False
        self.current_steps = 0
        self.current_temp = 25.0
        self.target_temp = 25.0
        self.task = None

    async def run_loop(self):
        print("🛠 Starting Internal Simulation Engine...")
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            # Simulate hardware behavior
            pwm = 150 if (iteration % 100) < 50 else 50
            steps_inc = 10
            self.current_steps += steps_inc
            
            # Physics with noise
            # Motor position roughly follows steps
            actual_pos = self.current_steps * 0.05 + random.uniform(-0.02, 0.02)
            
            # Temperature Control Logic (Per User Request)
            if self.current_temp < self.target_temp:
                # 1. Random increase (5,6,7,8,9,10)
                inc = random.randint(5, 10)
                self.current_temp += inc
                
                # Momentum Overshoot: High chance to "kick" above target when first reaching it
                if self.current_temp >= self.target_temp and random.random() < 0.7:
                    kick = random.randint(4, 12)
                    self.current_temp += kick
                    print(f"🚀 MOMENTUM OVERSHOOT: Thermal inertia kicked +{kick}°C above target!")
                else:
                    print(f"🌡 Heating: +{inc}°C -> {self.current_temp:.1f}°C")
                    
            elif self.current_temp > self.target_temp:
                # 2. Over-target handling: Start decreasing
                self.current_temp -= 1.0 # Steady cooling towards target
                if self.current_temp < self.target_temp:
                    self.current_temp = self.target_temp
                print(f"❄ Stabilizing: {self.current_temp:.1f}°C (Target: {self.target_temp}°C)")
            else:
                # 3. Constant Value: Maintain exactly
                # Occasionally inject a random spike to test "maintenance" behavior
                if random.random() < 0.10: # Increased to 10% chance per interval
                    spike = random.randint(5, 15)
                    self.current_temp += spike
                    print(f"🔥 THERMAL SPIKE: Temperature jumped +{spike}°C! System re-stabilizing...")

            payload = {
                "position": actual_pos,
                "temperature": self.current_temp,
                "pwm": pwm,
                "steps": self.current_steps
            }

            # Process via ingestion service
            db = SessionLocal()
            try:
                await ingestion_service.process_telemetry(db, payload, source="simulated")
                print(f"📡 Heartbeat [{iteration}]: Captured @ {time.strftime('%H:%M:%S')} | Temp: {self.current_temp:.1f}°C")
            finally:
                db.close()

            iteration += 1
            await asyncio.sleep(2)  # Simulating 2-second telemetry rate

    async def trigger_update(self):
        """Triggers a one-off telemetry update to broadcast changes immediately."""
        db = SessionLocal()
        try:
            actual_pos = self.current_steps * 0.05
            payload = {
                "position": actual_pos,
                "temperature": self.current_temp,
                "pwm": 0, # Neutral PWM for manual jump
                "steps": self.current_steps
            }
            await ingestion_service.process_telemetry(db, payload, source="simulated")
        finally:
            db.close()

    def start(self):
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.run_loop())

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()

    def set_target_position(self, target_pos: float):
        """Manually jumps the simulation to a specific position by calculating required steps."""
        self.current_steps = int(target_pos / 0.05)
        print(f"🎯 SIMULATION: Target position set to {target_pos}mm ({self.current_steps} steps)")

    def set_target_temperature(self, target_temp: float):
        """Sets the new target setpoint for the temperature controller."""
        self.target_temp = target_temp
        print(f"🎯 SIMULATION: System Target Setpoint -> {target_temp}°C")

simulation_engine = SimulationEngine()
