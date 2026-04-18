from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db.database import engine, Base, get_db, migrate_db, SessionLocal
from .services.ingestion_service import ingestion_service
from .services.simulation_service import simulation_engine
from .db import models
from .ml.metadata import load_metadata
from .ml.model import retrain_from_history, RETRAIN_INTERVAL_SECS
from .agents.orchestrator_agent import orchestrator as agent_orchestrator
from .agents.notification_agent import notification_agent
from .agents.chat_agent import chat_agent
from pydantic import BaseModel
import json
import asyncio

# Ensure tables are created
Base.metadata.create_all(bind=engine)

async def _periodic_retrain_task():
    """Background task: retrain model from live SQLite history every 30 minutes."""
    while True:
        await asyncio.sleep(RETRAIN_INTERVAL_SECS)
        print("[Retrain] Scheduled retraining check...")
        db = SessionLocal()
        try:
            retrain_from_history(db)
        except Exception as e:
            print(f"[Retrain] Background task error: {e}")
        finally:
            db.close()

from .services.recovery_monitor import background_recovery_monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB migration → wire WebSocket → start retrain timer
    migrate_db()
    ingestion_service.manager = manager
    # Auto-start simulation disabled to prioritize physical IoT stream.
    # simulation_engine.start() 
    asyncio.create_task(_periodic_retrain_task())
    asyncio.create_task(background_recovery_monitor())
    print(f"[Retrain] Periodic retraining scheduled every {RETRAIN_INTERVAL_SECS//60} minutes")
    yield
    # Shutdown
    simulation_engine.stop()


app = FastAPI(title="Agentic Digital Twin API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

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
        "current":     payload.current,   # Raw current passed for RCA engine
    }

    try:
        results = await ingestion_service.process_telemetry(db, pipeline_data, source="iot")

        analysis = results["analysis"]
        rca      = results.get("rca", {})

        return {
            "status": "ok",
            "source": "esp32",
            "mapped": {k: v for k, v in pipeline_data.items() if k != "current"},
            "analysis": {
                # ML layer
                "risk_score":     analysis.risk_score,
                "issue_detected": analysis.issue_detected,
                "anomaly":        analysis.anomaly_flag,
                "anomaly_score":  analysis.anomaly_score,
                "recommendation": analysis.recommendation,
                # RCA layer
                "rca": {
                    "root_cause":         rca.get("root_cause"),
                    "confidence_score":   rca.get("confidence_score"),
                    "severity":           rca.get("severity"),
                    "reasoning":          rca.get("reasoning", []),
                    "recommended_action": rca.get("recommended_action"),
                    "contributing_factors": rca.get("contributing_factors", []),
                }
            },
            "command": {
                "action": results.get("healing", {}).get("selected_action", "none"),
                "value": results.get("healing", {}).get("action_value", None)
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
        analysis = results["analysis"]
        rca      = results.get("rca", {})
        return {
            "status": "success",
            "analysis": {
                "risk_score":     analysis.risk_score,
                "issue_detected": analysis.issue_detected,
                "anomaly":        analysis.anomaly_flag,
                "anomaly_score":  analysis.anomaly_score,
                "recommendation": analysis.recommendation,
                "rca": rca,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket] Neural Link Established: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("[WebSocket] Neural Link Severed")

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
    import json as _json
    return {
        # ML layer
        "risk_score":        latest.risk_score,
        "issue_detected":    latest.issue_detected,
        "recommendation":    latest.recommendation,
        "anomaly":           latest.anomaly_flag,
        "anomaly_score":     latest.anomaly_score,
        "position_error":    latest.position_error,
        "temperature_error": latest.temperature_error,
        "timestamp":         latest.timestamp,
        # RCA layer
        "rca": {
            "root_cause":        latest.rca_root_cause,
            "confidence_score":  latest.rca_confidence,
            "severity":          latest.rca_severity,
            "reasoning":         _json.loads(latest.rca_reasoning or "[]"),
        }
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


# ─── ML Health Endpoints (Phase 4 & 5) ───────────────────────────────────────

@app.get("/ml/status", tags=["ML"])
def get_ml_status():
    """Returns current state of the trained Isolation Forest model."""
    try:
        meta = load_metadata()
        return {"status": "ok", "model": meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load ML metadata: {e}")


@app.post("/ml/retrain", tags=["ML"])
async def trigger_retrain(db: Session = Depends(get_db)):
    """
    Manually trigger a model retrain from live telemetry history.
    Only runs if ≥200 confirmed-normal DB samples exist.
    """
    try:
        success = retrain_from_history(db)
        if success:
            return {
                "status":   "retrained",
                "message":  "Model retrained from live history",
                "metadata": load_metadata(),
            }
        return {
            "status":  "skipped",
            "message": "Not enough confirmed-normal samples in DB yet (need ≥200)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrain error: {str(e)}")





# --- Agent Endpoints (4-Agent Integration) ---

@app.get('/agents/status', tags=['Agents'])
def get_agents_status():
    try:
        return agent_orchestrator.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/simulation/status", tags=["Simulation"])
async def get_sim_status():
    return {
        "is_running": simulation_engine.is_running,
        "mode": "ACTIVE" if simulation_engine.is_running else "IDLE"
    }

@app.post("/simulation/toggle", tags=["Simulation"])
async def toggle_simulation():
    if simulation_engine.is_running:
        simulation_engine.stop()
    else:
        simulation_engine.start()
    return {"status": "ok", "is_running": simulation_engine.is_running}
@app.post("/agents/chat", tags=["Agents"])
async def chat_with_machine(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handles conversational AI interaction with system awareness.
    """
    # Get latest telemetry and analytics for context
    latest_analysis = db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).first()
    latest_telemetry = db.query(models.TelemetryData).order_by(models.TelemetryData.timestamp.desc()).first()
    
    if latest_analysis and latest_telemetry:
        context = (
            f"Machine Status: {latest_analysis.alert_state or 'CLEAR'}. "
            f"Temperature: {latest_telemetry.actual_temperature:.1f}°C (Error: {latest_analysis.temperature_error:.1f}). "
            f"Position: {latest_telemetry.actual_position:.3f}mm (Error: {latest_analysis.position_error:.3f}). "
            f"Risk Score: {latest_analysis.risk_score:.2f}. "
            f"Last RCA: {latest_analysis.llm_explanation[:100] if latest_analysis.llm_explanation else 'No active faults'}..."
        )
    elif latest_telemetry:
         context = f"Telemetry active: Temp {latest_telemetry.actual_temperature:.1f}°C, Pos {latest_telemetry.actual_position:.3f}mm. Analytics pending."
    else:
        context = "No telemetry data recorded yet. The system is idle."

    response = await chat_agent.chat(
        user_message=request.message,
        chat_history=request.history,
        system_context=context
    )

    return {"response": response, "context_used": context}


@app.post('/agents/test-notify', tags=['Agents'])
async def test_notification():
    try:
        results = await notification_agent.send_test()
        return {'status': 'test_sent', 'channels': results, 'tip': 'Add TELEGRAM_TOKEN + TELEGRAM_CHAT_ID to .env to enable Telegram.'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from .api.endpoints import healing
app.include_router(healing.router, prefix="/healing", tags=["Self-Healing"])

from .api.endpoints import maintenance
app.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])

from .api.endpoints import loss
app.include_router(loss.router, prefix="/analytics", tags=["Analytics"])

from .api.endpoints import failure
app.include_router(failure.router, prefix="/failure", tags=["Diagnostics"])

from .api.endpoints import voice
app.include_router(voice.router, prefix="/voice", tags=["Machine Voice"])
