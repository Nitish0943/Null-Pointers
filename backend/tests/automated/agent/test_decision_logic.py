import pytest
import sys
import os
sys.path.append(os.getcwd())
from app.agents.machine_voice_engine import machine_voice_engine
from app.agents.loss_engine import loss_engine
from app.agents.self_healing_engine import self_healing_engine
from unittest.mock import MagicMock

def test_machine_voice_relevance():
    ml = {"anomaly": True}
    rca = {"root_cause": "Mechanical Friction", "severity": "HIGH"}
    msg = machine_voice_engine.generate_message(ml, rca)
    assert "resisting my motion" in msg.lower() or "friction" in msg.lower()
    assert "I" in msg

def test_production_loss_math():
    ml = {"anomaly": True}
    rca = {"severity": "CRITICAL"}
    res = loss_engine.process(MagicMock(), ml, rca, machine_id="test")
    assert res["cost_loss_inr"] > 0
    assert res["urgency"] == "High"
    assert res["recovery_priority"] == "Immediate"

def test_self_healing_trigger():
    ml = {"anomaly": True, "risk_score": 0.9}
    rca = {"root_cause": "Mechanical Friction", "severity": "HIGH"}
    telemetry = {"pwm": 128}
    mock_db = MagicMock()
    action = self_healing_engine.process(mock_db, telemetry, ml, rca, 2.5, 5.0)
    assert action is not None
    assert action["issue_detected"] is True
    assert action["selected_action"] != "none"
