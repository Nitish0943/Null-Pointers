import math
import time
from datetime import datetime

class DigitalTwinService:
    def __init__(self):
        # Motor Constants
        self.step_resolution = 0.05  # mm per step
        
        # Thermal State
        self.ambient_temp = 25.0
        self.k = 0.08  # System thermal constant (tuned for responsiveness)
        self.max_temp_gain = 80.0
        
        self.current_predicted_temp = 25.0
        self.last_update_time = time.time()

    def predict_motor_position(self, current_steps: int) -> float:
        """Linear mapping of steps to position."""
        return round(current_steps * self.step_resolution, 3)

    def predict_temperature(self, pwm: int) -> float:
        """
        Discrete-Time State Model:
        T_new = T_old + k * (T_target - T_old) * dt
        
        This makes the twin 'stick' to the physics even if PWM changes abruptly.
        """
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now

        # Limit dt to prevent huge jumps if the system was paused/slow
        dt = min(dt, 2.0) 

        # Target temperature at this PWM level
        t_target = self.ambient_temp + (pwm / 255.0) * self.max_temp_gain
        
        # Numerical integration (Euler method) for cooling/heating
        # Small k means slow heating, large k means fast heating
        change = (t_target - self.current_predicted_temp) * (1 - math.exp(-self.k * dt))
        self.current_predicted_temp += change
        
        return round(self.current_predicted_temp, 2)

twin_service = DigitalTwinService()

