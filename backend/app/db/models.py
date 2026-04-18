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
    source          = Column(String,  default="simulated")


