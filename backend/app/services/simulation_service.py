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
            
            # Temperature follows a noisy approach
            # Using a simple delta here for the data generator part
            self.current_temp += (pwm/255.0)*0.2 - 0.05 + random.uniform(-0.1, 0.1)
            
            # Inject anomaly occasionally (every 75 steps in this cycle)
            if iteration % 100 == 75:
                self.current_temp += 12.0
                print("⚠ SIMULATION: Injecting thermal anomaly!")

            payload = {
                "position": actual_pos,
                "temperature": self.current_temp,
                "pwm": pwm,
                "steps": self.current_steps
            }

            # Process via ingestion service
            db = SessionLocal()
            try:
                await ingestion_service.process_telemetry(db, payload)
                # Note: We don't broadcast here directly to keep it decoupled
                # The main API will handle broadcasting if desired, or we can add it
            finally:
                db.close()

            iteration += 1
            await asyncio.sleep(2)  # Simulating 2-second telemetry rate

    def start(self):
        if not self.is_running:
            self.task = asyncio.create_task(self.run_loop())

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()

simulation_engine = SimulationEngine()
