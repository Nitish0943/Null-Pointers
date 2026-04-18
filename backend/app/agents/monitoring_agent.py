"""
monitoring_agent.py — Monitoring Agent (Agent 1)

PURPOSE:
  Tracks alert state over a rolling window of telemetry readings.
  Prevents alert spam by debouncing single-reading spikes.
  Escalates severity when the same fault persists.
  Emits structured state-change events consumed by the Orchestrator.

STATE MACHINE:
  CLEAR      → risk < 0.3 for 3+ consecutive readings
  WARNING    → risk > 0.3 for 2+ consecutive readings (not yet confirmed)
  ACTIVE     → risk > 0.5 confirmed (2+ readings above threshold)
  ESCALATED  → ACTIVE for > 5 unresolved readings with same root cause
  RESOLVED   → Was ACTIVE, now CLEAR for 3 readings

EVENTS EMITTED (only on state transition):
  ALERT_NEW        → first time entering ACTIVE
  ALERT_ESCALATED  → ACTIVE → ESCALATED
  ALERT_RESOLVED   → ACTIVE/ESCALATED → CLEAR
  None             → no state change this cycle
"""

from collections import deque
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# ── Thresholds ─────────────────────────────────────────────────────────────────
WARNING_THRESHOLD    = 0.30   # risk_score above this → potential issue
ACTIVE_THRESHOLD     = 0.50   # risk_score above this → confirmed issue
CLEAR_THRESHOLD      = 0.25   # risk_score below this → system clearing
DEBOUNCE_READINGS    = 3      # # consecutive readings before state change
ESCALATION_READINGS  = 5      # # consecutive ACTIVE readings before escalating
RESOLVE_READINGS     = 3      # # consecutive CLEAR readings before resolving
WINDOW_SIZE          = 20     # rolling history kept in memory

# ── Alert States ───────────────────────────────────────────────────────────────
STATE_CLEAR     = "CLEAR"
STATE_WARNING   = "WARNING"
STATE_ACTIVE    = "ACTIVE"
STATE_ESCALATED = "ESCALATED"
STATE_RESOLVED  = "RESOLVED"   # transient — emitted once, then becomes CLEAR

# ── Alert Events ───────────────────────────────────────────────────────────────
EVENT_NEW        = "ALERT_NEW"
EVENT_ESCALATED  = "ALERT_ESCALATED"
EVENT_RESOLVED   = "ALERT_RESOLVED"


class MonitoringAgent:
    """
    Stateful alert monitoring agent.
    A single instance persists across all telemetry events (singleton pattern).
    """

    def __init__(self):
        self._risk_history:  deque = deque(maxlen=WINDOW_SIZE)
        self._root_history:  deque = deque(maxlen=WINDOW_SIZE)

        self._state:           str  = STATE_CLEAR
        self._consecutive:     int  = 0    # consecutive readings in current state direction
        self._clear_count:     int  = 0    # consecutive clear readings (for resolve)
        self._last_alert_at:   Optional[datetime] = None
        self._sustained_cause: Optional[str]      = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def observe(self, pipeline_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called once per telemetry event.
        Updates internal state and returns the current monitoring result.

        Args:
            pipeline_output: dict with keys ml_result, rca_result

        Returns:
            dict with alert_state, alert_event, alert_count,
                  sustained_root_cause, should_notify, should_explain
        """
        risk_score  = pipeline_output["ml_result"]["risk_score"]
        root_cause  = pipeline_output["rca_result"].get("root_cause", "Unknown")
        severity    = pipeline_output["rca_result"].get("severity", "LOW")

        self._risk_history.append(risk_score)
        self._root_history.append(root_cause)

        # Run state transition logic
        event = self._transition(risk_score, root_cause)

        # Decide if downstream agents should run
        should_notify  = self._should_notify(event)
        should_explain = self._should_explain(event, risk_score)

        result = {
            "alert_state":          self._state,
            "alert_event":          event,
            "alert_count":          self._consecutive,
            "sustained_root_cause": self._sustained_cause,
            "should_notify":        should_notify,
            "should_explain":       should_explain,
            "risk_trend":           self._compute_trend(),
            "checked_at":           datetime.now(timezone.utc).isoformat(),
        }

        if event:
            print(f"[Monitor] {event}: state={self._state}  risk={risk_score:.3f}  cause={root_cause}")

        return result

    def get_status(self) -> Dict[str, Any]:
        """Returns current monitoring snapshot (for /agents/status endpoint)."""
        return {
            "current_state":   self._state,
            "consecutive":     self._consecutive,
            "sustained_cause": self._sustained_cause,
            "last_alert_at":   self._last_alert_at.isoformat() if self._last_alert_at else None,
            "risk_history":    list(self._risk_history)[-10:],  # last 10
        }

    # ── State Machine ──────────────────────────────────────────────────────────

    def _transition(self, risk: float, root_cause: str) -> Optional[str]:
        """Evaluate state machine and return any emitted event (or None)."""
        prev_state = self._state

        if risk >= ACTIVE_THRESHOLD:
            self._clear_count = 0      # reset clear counter
            self._consecutive += 1

            # Track dominant root cause for escalation
            if self._consecutive == 1:
                self._sustained_cause = root_cause

            if self._state == STATE_CLEAR or self._state == STATE_WARNING:
                if self._consecutive >= DEBOUNCE_READINGS:
                    self._state = STATE_ACTIVE
                    self._last_alert_at = datetime.now(timezone.utc)
                    return EVENT_NEW
                else:
                    self._state = STATE_WARNING

            elif self._state == STATE_ACTIVE:
                if self._consecutive >= ESCALATION_READINGS:
                    self._state = STATE_ESCALATED
                    return EVENT_ESCALATED

        elif risk >= WARNING_THRESHOLD:
            self._clear_count = 0
            if self._state in (STATE_CLEAR,):
                self._consecutive += 1
                self._state = STATE_WARNING

        else:
            # Risk is low
            self._consecutive = 0
            if self._state in (STATE_ACTIVE, STATE_ESCALATED):
                self._clear_count += 1
                if self._clear_count >= RESOLVE_READINGS:
                    self._state = STATE_CLEAR
                    self._sustained_cause = None
                    self._clear_count = 0
                    return EVENT_RESOLVED
            else:
                self._clear_count += 1
                if self._clear_count >= RESOLVE_READINGS:
                    self._state = STATE_CLEAR

        return None

    # ── Decision Helpers ───────────────────────────────────────────────────────

    def _should_notify(self, event: Optional[str]) -> bool:
        """
        Notify only on significant state-change events.
        Prevents re-notifying on every telemetry cycle.
        """
        return event in (EVENT_NEW, EVENT_ESCALATED, EVENT_RESOLVED)

    def _should_explain(self, event: Optional[str], risk: float) -> bool:
        """
        Trigger LLM explanation on new or escalated alerts with sufficient confidence.
        LLM calls are expensive — only call when meaningful.
        """
        return event in (EVENT_NEW, EVENT_ESCALATED) and risk > 0.5

    def _compute_trend(self) -> str:
        """Returns 'RISING', 'FALLING', or 'STABLE' based on last 5 risk scores."""
        if len(self._risk_history) < 4:
            return "STABLE"
        recent = list(self._risk_history)
        first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
        second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        diff = second_half - first_half
        if diff > 0.05:
            return "RISING"
        elif diff < -0.05:
            return "FALLING"
        return "STABLE"


# ── Singleton ──────────────────────────────────────────────────────────────────
monitoring_agent = MonitoringAgent()
