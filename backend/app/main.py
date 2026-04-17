from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from .db.database import engine, Base, get_db, migrate_db
from .services.ingestion_service import ingestion_service
from .services.simulation_service import simulation_engine
from .db import models
from pydantic import BaseModel
import json

# Ensure tables are created
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run DB migration, wire services, start simulation
    migrate_db()
    ingestion_service.manager = manager
    simulation_engine.start()
    yield
    # Shutdown
    simulation_engine.stop()


app = FastAPI(title="Agentic Digital Twin API", lifespan=lifespan)

class TelemetryIn(BaseModel):
    """
    Schema for simulator / manual POST requests.
    Fields match the existing digital twin pipeline vocabulary.
    """
    position: float
    temperature: float
    pwm: int
    steps: int

# ─── ESP32 Device Schema ──────────────────────────────────────────────────────
class ESP32TelemetryIn(BaseModel):
    """
    Schema that EXACTLY matches the JSON payload sent by the ESP32:
      { "tilt": float, "temperature": float, "current": float }

    WHY this is a separate model:
      The 422 error occurred because FastAPI validated the request body against
      TelemetryIn (which expects 'position', 'pwm', 'steps') — fields the ESP32
      doesn't send. FastAPI rejects any mismatch before reaching your code.

    FIELD MAPPING to Digital Twin pipeline:
      tilt        → position  (tilt angle in degrees ≈ shaft position proxy)
      temperature → temperature (direct 1-to-1 mapping)
      current     → pwm  (motor current draw ≈ effort / control signal proxy,
                          scaled to 0-255 range for compatibility)
    """
    tilt: float        # Tilt sensor reading (°) — maps to motor position
    temperature: float # Heater/motor temperature (°C) — direct mapping
    current: float     # Motor current draw (A) — maps to PWM/effort signal

# ─── ESP32 Endpoint ───────────────────────────────────────────────────────────
@app.post("/esp32/telemetry", tags=["ESP32"])
async def ingest_esp32_telemetry(payload: ESP32TelemetryIn, db: Session = Depends(get_db)):
    """
    Accepts telemetry from an ESP32 device and routes it into the full pipeline:
      ESP32 Data → Field Mapping → Digital Twin → ML Inference → DB → WebSocket

    Device sends:  { "tilt": 12.4, "temperature": 38.5, "current": 1.2 }
    Returns:       { "status": "ok", "source": "esp32", "analysis": {...} }
    """
    # Log incoming device data for debugging
    print(f"[ESP32] Received → tilt={payload.tilt}°  temp={payload.temperature}°C  current={payload.current}A")

    # ── Field Mapping ──────────────────────────────────────────────────────────
    # tilt (°) → position (mm proxy): 1° tilt ≈ 1 unit of positional displacement
    mapped_position = payload.tilt

    # current (A) → pwm (0-255): Clamp to realistic motor current range 0-5A,
    # then scale linearly to 0-255 PWM range
    mapped_pwm = int(min(255, max(0, (payload.current / 5.0) * 255)))

    # steps: not available from ESP32 — estimate from tilt (1° ≈ 20 steps)
    mapped_steps = int(abs(payload.tilt) * 20)

    # Normalized pipeline payload
    pipeline_data = {
        "position":    mapped_position,
        "temperature": payload.temperature,
        "pwm":         mapped_pwm,
        "steps":       mapped_steps,
    }

    try:
        results = await ingestion_service.process_telemetry(db, pipeline_data)

        analysis = results["analysis"]
        return {
            "status":  "ok",
            "source":  "esp32",
            "mapped":  pipeline_data,           # Show what was sent to the twin
            "analysis": {
                "risk_score":     analysis.risk_score,
                "issue_detected": analysis.issue_detected,
                "anomaly":        analysis.anomaly_flag,
                "anomaly_score":  analysis.anomaly_score,
                "recommendation": analysis.recommendation,
            }
        }
    except Exception as e:
        print(f"[ESP32] Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# ─── Simulator / Manual Endpoint ──────────────────────────────────────────────
@app.post("/telemetry", tags=["Simulator"])
async def ingest_telemetry(payload: TelemetryIn, db: Session = Depends(get_db)):
    try:
        results = await ingestion_service.process_telemetry(db, payload.dict())
        return {"status": "success", "analysis": results['analysis']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass # Connection might be closed

manager = ConnectionManager()

@app.get("/")
def read_root():
    return {"status": "online", "project": "Agentic Digital Twin"}

@app.post("/telemetry")
async def ingest_telemetry(payload: TelemetryIn, db: Session = Depends(get_db)):
    try:
        # ingestion_service now handles processing, DB storage, AND broadcasting
        results = await ingestion_service.process_telemetry(db, payload.dict())
        return {"status": "success", "analysis": results['analysis']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    latest = db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).first()
    if not latest:
        return {"risk_score": 0.0, "status": "No data"}
    return {
        "risk_score":       latest.risk_score,
        "issue_detected":   latest.issue_detected,
        "recommendation":   latest.recommendation,
        "anomaly":          latest.anomaly_flag,
        "anomaly_score":    latest.anomaly_score,
        "position_error":   latest.position_error,
        "temperature_error":latest.temperature_error,
        "timestamp":        latest.timestamp
    }

@app.get("/history")
def get_history(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.TelemetryData).order_by(models.TelemetryData.timestamp.desc()).limit(limit).all()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


