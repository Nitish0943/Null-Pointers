from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from .db.database import engine, Base, get_db
from .services.ingestion_service import ingestion_service
from .db import models
from pydantic import BaseModel
import json

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Digital Twin API")

class TelemetryIn(BaseModel):
    position: float
    temperature: float
    pwm: int
    steps: int

# WebSocket Manager
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
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/")
def read_root():
    return {"status": "online", "project": "Agentic Digital Twin"}

@app.post("/telemetry")
async def ingest_telemetry(payload: TelemetryIn, db: Session = Depends(get_db)):
    try:
        results = await ingestion_service.process_telemetry(db, payload.dict())
        
        # Prepare broadcast payload
        broadcast_data = {
            "type": "TELEMETRY_UPDATE",
            "data": {
                "actual": payload.dict(),
                "predicted": {
                    "position": results['prediction'].predicted_position,
                    "temperature": results['prediction'].predicted_temperature
                },
                "analysis": {
                    "risk_score": results['analysis'].risk_score,
                    "recommendation": results['analysis'].recommendation
                }
            }
        }
        await manager.broadcast(broadcast_data)
        
        return {"status": "success", "analysis": results['analysis']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    latest = db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).first()
    if not latest:
        return {"risk_score": 0.0, "status": "No data"}
    return latest

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
