from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from datetime import datetime
from .database import Base

class TelemetryData(Base):
    __tablename__ = "telemetry_data"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    actual_position = Column(Float)
    actual_temperature = Column(Float)
    pwm = Column(Integer)
    steps = Column(Integer)
    source = Column(String, default="simulated") # 'simulated' or 'iot'

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    predicted_position = Column(Float)
    predicted_temperature = Column(Float)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    position_error = Column(Float)
    temperature_error = Column(Float)
    risk_score = Column(Float)
    issue_detected = Column(Boolean)
    recommendation = Column(String)
    # ML anomaly fields
    anomaly_flag = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    # RCA fields
    rca_root_cause  = Column(String,  default="No Fault Detected")
    rca_confidence  = Column(Float,   default=0.0)
    rca_severity    = Column(String,  default="LOW")
    rca_reasoning   = Column(Text,    default="[]")  # JSON array stored as text
    # Agent fields (added by 4-agent integration)
    llm_explanation = Column(Text,    default=None)  # Gemini-generated maintenance report
    alert_state     = Column(String,  default="CLEAR")  # Monitoring agent alert state
    machine_voice   = Column(Text,    default=None)   # Machine self-explanation
    source          = Column(String,  default="simulated")

class HealingEvent(Base):
    """
    Logs autonomous self-healing interventions, actions taken, and verification results.
    """
    __tablename__ = "healing_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    anomaly_detected = Column(String)       # e.g., "Overheating", "Mechanical friction rise"
    action_taken = Column(String)           # e.g., "reduce_pwm"
    action_value = Column(Integer, nullable=True) # e.g., 120
    confidence = Column(Float)
    command_sent = Column(Boolean, default=True)
    verification_status = Column(String, default="verifying") # verifying, recovered, failed, escalated
    recovery_time_sec = Column(Float, nullable=True)

class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, unique=True, index=True)
    machine_id = Column(String, index=True)
    priority = Column(String) # Low, Medium, High, Critical
    issue = Column(String)
    recommended_part = Column(String)
    repair_eta = Column(String)
    downtime_window = Column(String)
    status = Column(String, default="Open") # Open, In Progress, Closed
    severity = Column(String, nullable=True) # LOW, MEDIUM, HIGH, CRITICAL
    loss_estimate_inr = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ProductionLoss(Base):
    __tablename__ = "production_losses"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    machine_id = Column(String, index=True)
    estimated_downtime_min = Column(Integer)
    units_lost = Column(Integer)
    cost_loss_inr = Column(Float)
    urgency = Column(String) # Low, Medium, High, Critical
    recovery_priority = Column(String) # Immediate, Normal, Scheduled
