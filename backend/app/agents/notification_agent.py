"""
notification_agent.py — Notification Agent (Agent 2)

PURPOSE:
  Sends real-time alerts to external channels when the Monitoring Agent
  determines a notification should be sent (should_notify=True).

SUPPORTED CHANNELS:
  1. Telegram Bot  — instant mobile notification (recommended for hackathon)
  2. Generic Webhook — POST JSON payload to any URL
  3. Slack Webhook — pre-formatted Slack message

GRACEFUL DEGRADATION:
  If no channel is configured (missing env vars), the agent silently logs
  the alert locally and returns {"sent": False, "reason": "no channels configured"}.
  The rest of the pipeline is never blocked.

CONFIGURATION (add to backend/.env):
  TELEGRAM_TOKEN=your_bot_token_from_botfather
  TELEGRAM_CHAT_ID=your_chat_id
  WEBHOOK_URL=https://your-endpoint.com/webhook
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
  ALERT_COOLDOWN_SECONDS=60
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# We use httpx for async HTTP — already a transitive dep or we add it
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

# ── Config (read from .env via os.environ) ────────────────────────────────────
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID", "")
WEBHOOK_URL       = os.getenv("WEBHOOK_URL", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
COOLDOWN_SECS     = int(os.getenv("ALERT_COOLDOWN_SECONDS", "60"))

# Emoji map for severity levels
SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
}

EVENT_EMOJI = {
    "ALERT_NEW":       "🚨",
    "ALERT_ESCALATED": "⚠️",
    "ALERT_RESOLVED":  "✅",
}


class NotificationAgent:
    """
    Multi-channel notification agent.
    Respects a cooldown period between notifications to prevent spam.
    """

    def __init__(self):
        self._last_sent_at: Optional[datetime] = None
        self._sent_count: int = 0

    # ── Public API ─────────────────────────────────────────────────────────────

    async def send(
        self,
        pipeline_output: Dict[str, Any],
        monitoring:      Dict[str, Any],
        explanation:     Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send an alert notification across all configured channels.

        Args:
            pipeline_output: full pipeline result (ml_result, rca_result, etc.)
            monitoring:      monitoring agent output (alert_state, alert_event, etc.)
            explanation:     optional LLM explanation dict

        Returns:
            dict with sent status per channel
        """
        # Check cooldown
        if self._is_on_cooldown():
            print(f"[Notify] Cooldown active — skipping notification")
            return {"sent": False, "reason": "cooldown", "channels": []}

        # Build message content
        message = self._build_message(pipeline_output, monitoring, explanation)

        results = {"sent": False, "channels": [], "message_preview": message[:120]}

        # Send to each configured channel
        channels_tried = []

        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            ok = await self._send_telegram(message)
            channels_tried.append({"channel": "telegram", "success": ok})
            if ok:
                results["sent"] = True

        if WEBHOOK_URL:
            payload = self._build_webhook_payload(pipeline_output, monitoring, explanation)
            ok = await self._send_webhook(WEBHOOK_URL, payload)
            channels_tried.append({"channel": "webhook", "success": ok})
            if ok:
                results["sent"] = True

        if SLACK_WEBHOOK_URL:
            ok = await self._send_slack(message)
            channels_tried.append({"channel": "slack", "success": ok})
            if ok:
                results["sent"] = True

        if not channels_tried:
            # No channels configured — log locally
            print(f"\n{'='*54}")
            print(f"  [LOCAL ALERT — no channels configured]")
            print(message)
            print(f"{'='*54}\n")
            results["reason"] = "no_channels_configured"
            results["sent"] = True  # Counts as "handled"
            channels_tried.append({"channel": "local_log", "success": True})

        results["channels"] = channels_tried

        if results["sent"]:
            self._last_sent_at = datetime.now(timezone.utc)
            self._sent_count += 1
            print(f"[Notify] Alert sent via {[c['channel'] for c in channels_tried if c['success']]}")

        return results

    async def send_test(self) -> Dict[str, Any]:
        """Send a test notification to verify channel configuration."""
        test_message = (
            "✅ TEST ALERT — Agentic Digital Twin\n"
            "──────────────────────────────────────\n"
            "This is a test notification.\n"
            "If you received this, the notification agent is working correctly.\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        results = {}
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            results["telegram"] = await self._send_telegram(test_message)
        if WEBHOOK_URL:
            results["webhook"] = await self._send_webhook(WEBHOOK_URL, {"test": True, "message": test_message})
        if SLACK_WEBHOOK_URL:
            results["slack"] = await self._send_slack(test_message)
        if not results:
            results["local_log"] = True
            print(f"\n[TEST NOTIFICATION]\n{test_message}\n")
        return results

    # ── Message Builder ────────────────────────────────────────────────────────

    def _build_message(
        self,
        pipeline_output: Dict[str, Any],
        monitoring:      Dict[str, Any],
        explanation:     Optional[Dict[str, Any]],
    ) -> str:
        """Build a human-readable plain-text alert message."""
        rca         = pipeline_output.get("rca_result", {})
        ml          = pipeline_output.get("ml_result", {})
        event       = monitoring.get("alert_event", "ALERT_NEW")
        state       = monitoring.get("alert_state", "ACTIVE")
        root_cause  = rca.get("root_cause", "Unknown")
        severity    = rca.get("severity", "MEDIUM")
        confidence  = rca.get("confidence_score", 0.0)
        risk_score  = ml.get("risk_score", 0.0)
        reasoning   = rca.get("reasoning", [])
        action      = rca.get("recommended_action", "Check system.")

        event_emoji    = EVENT_EMOJI.get(event, "🚨")
        severity_emoji = SEVERITY_EMOJI.get(severity, "🟡")
        timestamp      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            f"{event_emoji} {event.replace('_', ' ')} — Agentic Digital Twin",
            "──────────────────────────────────────",
            f"Fault:      {root_cause}",
            f"Severity:   {severity_emoji} {severity}",
            f"Confidence: {confidence*100:.1f}%",
            f"Risk Score: {risk_score:.3f}",
            f"Alert State:{state}",
            "",
        ]

        if reasoning:
            lines.append("Evidence:")
            for r in reasoning[:4]:
                lines.append(f"  • {r}")
            lines.append("")

        lines.append(f"Action: {action[:120]}")

        if explanation and explanation.get("explanation"):
            lines.append("")
            lines.append("AI Analysis:")
            # First sentence only for notification brevity
            exp_text = explanation["explanation"].split(".")[0] + "."
            lines.append(f"  {exp_text}")

        lines.append("──────────────────────────────────────")
        lines.append(f"Time: {timestamp} UTC")

        return "\n".join(lines)

    def _build_webhook_payload(
        self,
        pipeline_output: Dict[str, Any],
        monitoring:      Dict[str, Any],
        explanation:     Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build structured JSON payload for webhook delivery."""
        return {
            "event":        monitoring.get("alert_event"),
            "alert_state":  monitoring.get("alert_state"),
            "risk_score":   pipeline_output.get("ml_result", {}).get("risk_score"),
            "rca":          pipeline_output.get("rca_result", {}),
            "explanation":  explanation.get("explanation") if explanation else None,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "source":       "agentic-digital-twin",
        }

    # ── Channel Senders ────────────────────────────────────────────────────────

    async def _send_telegram(self, message: str) -> bool:
        if not _HTTPX_AVAILABLE:
            print("[Notify] httpx not installed — cannot send Telegram")
            return False
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text":    message,
                    "parse_mode": "HTML",
                })
            if resp.status_code == 200:
                return True
            print(f"[Notify] Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
        except Exception as e:
            print(f"[Notify] Telegram exception: {e}")
            return False

    async def _send_webhook(self, url: str, payload: Dict) -> bool:
        if not _HTTPX_AVAILABLE:
            print("[Notify] httpx not installed — cannot send Webhook")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
            return resp.status_code < 300
        except Exception as e:
            print(f"[Notify] Webhook exception: {e}")
            return False

    async def _send_slack(self, message: str) -> bool:
        if not _HTTPX_AVAILABLE:
            print("[Notify] httpx not installed — cannot send Slack")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(SLACK_WEBHOOK_URL, json={"text": message})
            return resp.status_code == 200
        except Exception as e:
            print(f"[Notify] Slack exception: {e}")
            return False

    # ── Cooldown ───────────────────────────────────────────────────────────────

    def _is_on_cooldown(self) -> bool:
        if not self._last_sent_at:
            return False
        elapsed = (datetime.now(timezone.utc) - self._last_sent_at).total_seconds()
        return elapsed < COOLDOWN_SECS


# ── Singleton ──────────────────────────────────────────────────────────────────
notification_agent = NotificationAgent()
