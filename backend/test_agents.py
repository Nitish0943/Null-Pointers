import sys
sys.path.insert(0, '.')

print("Testing agent imports...")
from app.agents.monitoring_agent import monitoring_agent
print("  [OK] MonitoringAgent")
from app.agents.notification_agent import notification_agent
print("  [OK] NotificationAgent")
from app.agents.explanation_agent import explanation_agent
print("  [OK] ExplanationAgent")
from app.agents.orchestrator_agent import orchestrator
print("  [OK] OrchestratorAgent")
from app.agents import orchestrator as orch_import
print("  [OK] agents package __init__")

print()
print("Testing monitoring state machine (5 readings)...")
fake_pipeline = {
    "ml_result":  {"risk_score": 0.8, "anomaly": True, "anomaly_score": 0.9, "issue_detected": True},
    "rca_result": {"root_cause": "Mechanical Jam", "confidence_score": 0.85, "severity": "HIGH",
                   "reasoning": ["High current", "Low movement"], "recommended_action": "Inspect lead screw."},
}

for i in range(1, 6):
    r = monitoring_agent.observe(fake_pipeline)
    print(f"  Reading {i}: state={r['alert_state']}  event={r['alert_event']}  notify={r['should_notify']}  explain={r['should_explain']}")

print()
print("Testing rule-based explanation fallback...")
import asyncio

async def test_explain():
    exp = await explanation_agent.explain(fake_pipeline, r)
    if exp:
        print(f"  Source  : {exp['source']}")
        print(f"  Preview : {exp['explanation'][:120]}...")
    else:
        print("  No explanation (below confidence threshold)")

asyncio.run(test_explain())

print()
print("Testing orchestrator.get_status()...")
status = orchestrator.get_status()
print(f"  Orchestrator cycles: {status['orchestrator']['total_cycles']}")
print(f"  Monitoring state   : {status['monitoring']['current_state']}")
print(f"  Explanation config : {status['explanation']}")

print()
print("ALL TESTS PASSED — agents are fully integrated")
