import math
from datetime import datetime

class DigitalTwinService:
    def __init__(self):
        # Motor Constants
        self.step_resolution = 0.05  # mm per step
        self.last_position = 0.0
        
        # Thermal Constants
        self.ambient_temp = 25.0
        self.k = 0.05  # Cooling constant
        self.heating_rate = 0.2  # Degrees per PWM second
        self.last_predicted_temp = 25.0

    def predict_motor_position(self, current_steps: int) -> float:
        """
        Simple kinematic model: Position = Steps * Resolution
        """
        return current_steps * self.step_resolution

    def predict_temperature(self, pwm: int, dt: float = 1.0) -> float:
        """
        Exponential Heating/Cooling Model:
        T(t+1) = T(t) + (Heating - Cooling) * dt
        """
        # Heating part based on PWM (0-255)
        heating = (pwm / 255.0) * self.heating_rate
        
        # Cooling part (Newton's Law of Cooling)
        cooling = self.k * (self.last_predicted_temp - self.ambient_temp)
        
        predicted_temp = self.last_predicted_temp + (heating - cooling) * dt
        self.last_predicted_temp = max(self.ambient_temp, predicted_temp)
        
        return self.last_predicted_temp

twin_service = DigitalTwinService()
