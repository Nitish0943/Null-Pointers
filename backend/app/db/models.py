from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
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
