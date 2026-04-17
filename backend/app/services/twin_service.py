import math
import time
from datetime import datetime

class DigitalTwinService:
    def __init__(self):
        # Motor Constants
        self.step_resolution = 0.05  # mm per step
        self.last_position = 0.0
        
        # Thermal Constants
        self.ambient_temp = 25.0
        self.k = 0.05  # System cooling/heating constant
        self.max_temp_gain = 80.0  # Max temp reach at 100% PWM
        self.start_time = time.time()
        self.last_predicted_temp = 25.0

    def predict_motor_position(self, current_steps: int) -> float:
        """
        Simulate position based on step count: Position = Steps * Resolution
        """
        return round(current_steps * self.step_resolution, 3)

    def predict_temperature(self, pwm: int, elapsed_time: float = None) -> float:
        """
        Exponential Heating Model:
        T(t) = T_env + (T_target - T_env) * (1 - e^(-k*t))
        """
        if elapsed_time is None:
            elapsed_time = time.time() - self.start_time

        # Target temperature depends on PWM power (0-255)
        # mapped to a temperature range above ambient
        t_target = self.ambient_temp + (pwm / 255.0) * self.max_temp_gain
        
        # Calculate prediction using the exponential approach formula
        # T(t) = T_env + delta_T * (1 - exp(-k * t))
        temp_rise = (t_target - self.ambient_temp) * (1 - math.exp(-self.k * elapsed_time))
        predicted_temp = self.ambient_temp + temp_rise
        
        self.last_predicted_temp = predicted_temp
        return round(predicted_temp, 2)

twin_service = DigitalTwinService()

