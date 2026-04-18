"""
orchestrator_agent.py — Orchestrator Agent (Agent 4)

PURPOSE:
  The central coordinator that runs on every telemetry event and decides:
    1. What is the current monitoring state? (MonitoringAgent)
    2. Should we generate an LLM explanation? (ExplanationAgent — if fault confirmed)
    3. Should we send a notification? (NotificationAgent — if event triggered)
    4. What enriched payload goes out to WebSocket + DB?

DESIGN PATTERN: ReAct (Reason + Act)
  Observe  → MonitoringAgent provides alert state
  Reason   → Orchestrator decides which agents to invoke
  Act      → ExplanationAgent + NotificationAgent execute if needed
  Return   → Enriched result for downstream (WebSocket, DB, API)

PERFORMANCE:
  - Monitoring agent: synchronous, O(1), ~0.1ms
  - Explanation agent: only runs on ALERT_NEW / ALERT_ESCALATED events
    (not every 2-second telemetry cycle)
  - Notification agent: only runs when should_notify=True
  - Worst case latency (all agents active): ~1-2s (Gemini API call)
  - Normal cycle latency (no fault): <1ms overhead
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .monitoring_agent   import monitoring_agent
from .explanation_agent  import explanation_agent
from .notification_agent import notification_agent


class OrchestratorAgent:
    """
    Coordinates all sub-agents and returns an enriched result
    that gets merged into the telemetry pipeline output.
    """

    def __init__(self):
        self._cycle_count: int = 0
        self._alert_count: int = 0
        self._last_explanation: Optional[Dict] = None

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run(self, pipeline_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration loop — called once per telemetry event.

        Args:
            pipeline_output: dict containing:
                ml_result:  {risk_score, anomaly, anomaly_score, issue_detected}
                rca_result: {root_cause, confidence_score, severity, reasoning, ...}
                actual:     {position, temperature, current}
                predicted:  {position, temperature}
                pos_error:  float
                temp_error: float

        Returns:
            orchestrator_result dict with:
                monitoring:        alert state + event
                explanation:       LLM report (or None)
                notification_sent: bool
                priority:          LOW | MEDIUM | HIGH | CRITICAL
                agent_summary:     human-readable one-liner
        """
        self._cycle_count += 1

        # ── Step 1: Observe ────────────────────────────────────────────────────
        # MonitoringAgent updates its state machine and emits events
        monitoring = monitoring_agent.observe(pipeline_output)
        alert_event = monitoring.get("alert_event")
        alert_state = monitoring.get("alert_state")

        # ── Step 2: Reason ─────────────────────────────────────────────────────
        # Decide which agents to activate this cycle
        run_explanation  = monitoring.get("should_explain", False)
        run_notification = monitoring.get("should_notify", False)

        # ── Step 3: Act ────────────────────────────────────────────────────────
        explanation = None
        if run_explanation:
            try:
                explanation = await explanation_agent.explain(pipeline_output, monitoring)
                if explanation:
                    self._last_explanation = explanation
                    print(f"[Orchestrator] Explanation generated: {explanation['source']}")
            except Exception as e:
                print(f"[Orchestrator] Explanation agent error: {e}")

        notification_result = {"sent": False, "channels": []}
        if run_notification:
            try:
                notification_result = await notification_agent.send(
                    pipeline_output, monitoring, explanation
                )
                if notification_result.get("sent"):
                    self._alert_count += 1
                    print(f"[Orchestrator] Notification sent (total: {self._alert_count})")
            except Exception as e:
                print(f"[Orchestrator] Notification agent error: {e}")

        # ── Step 4: Compute Priority ───────────────────────────────────────────
        priority = self._compute_priority(monitoring, pipeline_output)

        # ── Step 5: Build Summary ──────────────────────────────────────────────
        agent_summary = self._build_summary(monitoring, explanation, notification_result)

        if alert_event:
            print(f"[Orchestrator] Cycle {self._cycle_count}: {agent_summary}")

        return {
            "monitoring": {
                "alert_state":          alert_state,
                "alert_event":          alert_event,
                "alert_count":          monitoring.get("alert_count"),
                "sustained_root_cause": monitoring.get("sustained_root_cause"),
                "risk_trend":           monitoring.get("risk_trend"),
            },
            "explanation": {
                "available":    explanation is not None,
                "text":         explanation.get("explanation") if explanation else None,
                "source":       explanation.get("source") if explanation else None,
                "generated_at": explanation.get("generated_at") if explanation else None,
            } if explanation else None,
            "notification": {
                "sent":     notification_result.get("sent", False),
                "channels": notification_result.get("channels", []),
            },
            "priority":      priority,
            "agent_summary": agent_summary,
            "cycle":         self._cycle_count,
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns orchestrator + all sub-agent statuses for /agents/status."""
        return {
            "orchestrator": {
                "total_cycles":    self._cycle_count,
                "total_alerts":    self._alert_count,
                "checked_at":      datetime.now(timezone.utc).isoformat(),
            },
            "monitoring":    monitoring_agent.get_status(),
            "explanation":   explanation_agent.get_status(),
            "notification": {
                "cooldown_seconds": notification_agent._is_on_cooldown(),
                "total_sent":       notification_agent._sent_count,
            },
        }

    # ── Priority Computation ───────────────────────────────────────────────────

    def _compute_priority(
        self,
        monitoring:      Dict[str, Any],
        pipeline_output: Dict[str, Any],
    ) -> str:
        """
        Determines event priority for frontend display and routing.
        Combines alert state + RCA severity + risk score.
        """
        alert_state = monitoring.get("alert_state", "CLEAR")
        severity    = pipeline_output.get("rca_result", {}).get("severity", "LOW")
        risk_score  = pipeline_output.get("ml_result",  {}).get("risk_score", 0.0)

        if alert_state == "ESCALATED" or severity == "CRITICAL":
            return "CRITICAL"
        elif alert_state == "ACTIVE" and (severity == "HIGH" or risk_score > 0.7):
            return "HIGH"
        elif alert_state in ("ACTIVE", "WARNING") or risk_score > 0.4:
            return "MEDIUM"
        return "LOW"

    # ── Summary Builder ────────────────────────────────────────────────────────

    def _build_summary(
        self,
        monitoring:           Dict[str, Any],
        explanation:          Optional[Dict],
        notification_result:  Dict,
    ) -> str:
        """One-line human-readable summary of what happened this cycle."""
        state  = monitoring.get("alert_state", "CLEAR")
        event  = monitoring.get("alert_event")
        cause  = monitoring.get("sustained_root_cause", "")
        exp    = "LLM ✓" if explanation else ""
        notif  = "notified ✓" if notification_result.get("sent") else ""

        extras = " | ".join(filter(None, [exp, notif]))
        extras = f" [{extras}]" if extras else ""

        if event:
            return f"{event}: {state} — {cause}{extras}"
        return f"state={state}"


# ── Singleton ──────────────────────────────────────────────────────────────────
orchestrator = OrchestratorAgent()
