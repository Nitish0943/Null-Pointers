import pytest
import sys
import os
sys.path.append(os.getcwd())
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_telemetry_ingestion():
    # Valid simulated telemetry
    payload = {
        "timestamp": 1712345678,
        "actual_position": 50.5,
        "actual_temperature": 40.0,
        "pwm": 128,
        "steps": 1000,
        "source": "test"
    }
    response = client.post("/telemetry", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "analysis" in response.json()

def test_analytics_endpoint():
    # Ingest one point first
    client.post("/telemetry", json={
        "timestamp": 1712345679,
        "actual_position": 50.5,
        "actual_temperature": 40.0,
        "pwm": 128,
        "steps": 1000,
        "source": "test"
    })
    response = client.get("/analytics")
    assert response.status_code == 200
    assert "risk_score" in response.json()
    assert "rca" in response.json()

def test_history_endpoint():
    response = client.get("/history?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_voice_explain():
    # Payload for manual explain
    payload = {"trigger": "user_query"}
    response = client.post("/voice/explain", json=payload)
    assert response.status_code == 200
    assert "voice_message" in response.json()

def test_failure_replay():
    # Note: Requires recent data in DB
    response = client.post("/failure/replay", json={"machine_id": "simulated"})
    assert response.status_code == 200
    assert "past_events" in response.json()
