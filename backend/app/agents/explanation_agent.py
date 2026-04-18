"""
explanation_agent.py — LLM Explanation Agent (Agent 3)

PURPOSE:
  Uses Google Gemini to generate a concise, plain-language maintenance report
  when a fault is detected. Makes the system "genuinely agentic" — it can
  explain its reasoning in natural language that a field technician can act on.

TRIGGER:
  Only runs when monitoring_agent says should_explain=True AND
  rca confidence is above EXPLANATION_MIN_CONFIDENCE.

  This prevents:
    - Expensive LLM calls on every telemetry cycle
    - Explanations for low-confidence / uncertain diagnoses

GRACEFUL DEGRADATION:
  If GEMINI_API_KEY is not set, or if the API call fails, the agent returns
  a structured fallback explanation built from the RCA data without LLM.
  The pipeline never blocks.

CONFIGURATION (add to backend/.env):
  GEMINI_API_KEY=your_api_key_from_aistudio.google.com
  GEMINI_MODEL=gemini-1.5-flash
  EXPLANATION_MIN_CONFIDENCE=0.6
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# ── Config ─────────────────────────────────────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL       = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MIN_CONFIDENCE     = float(os.getenv("EXPLANATION_MIN_CONFIDENCE", "0.6"))

# Try to import Gemini SDK (new google.genai package)
try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    _GEMINI_AVAILABLE = True
except ImportError:
    try:
        # Fallback to legacy package (shows FutureWarning but still works)
        import google.generativeai as genai_legacy
        _GEMINI_AVAILABLE = True
        _USE_LEGACY = True
    except ImportError:
        _GEMINI_AVAILABLE = False
_USE_LEGACY = False  # will reset below if needed

# ── Prompt Template ────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """You are an industrial maintenance AI assistant for a motor-heater subsystem digital twin.

FAULT DETECTED:
  Root Cause:  {root_cause}
  Confidence:  {confidence:.1%}
  Severity:    {severity}
  Alert State: {alert_state}

TELEMETRY DATA:
  Actual Position:    {position:.3f} mm
  Actual Temperature: {temperature:.1f} °C
  Position Error:     {pos_error:.3f} mm (deviation from digital twin prediction)
  Temperature Error:  {temp_error:.1f} °C (deviation from digital twin prediction)
  ML Anomaly Score:   {anomaly_score:.3f} / 1.0

TRIGGERED DETECTION CONDITIONS:
{reasoning_list}

Write a concise maintenance report in exactly 3 short paragraphs:
  Paragraph 1: What is happening physically and why (technical but clear)
  Paragraph 2: The immediate action the operator must take RIGHT NOW
  Paragraph 3: Long-term recommendation to prevent this from recurring

Rules:
  - Maximum 150 words total
  - Use plain language a field technician can understand
  - Be specific about what to check (not generic advice)
  - Do not repeat the fault name in every sentence
"""


class ExplanationAgent:
    """
    LLM-powered fault explanation agent using Google Gemini.
    """

    def __init__(self):
        self._client = None
        self._call_count: int = 0
        self._last_explanation: Optional[Dict] = None
        self._configured = False

        if _GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                from google import genai as gai
                self._client = gai.Client(api_key=GEMINI_API_KEY)
                self._model_name = GEMINI_MODEL
                self._use_new_sdk = True
                self._configured = True
                print(f"[Explanation] Gemini configured (new SDK): model={GEMINI_MODEL}")
            except Exception:
                # Try legacy SDK as fallback
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=GEMINI_API_KEY)
                    self._client = genai_legacy.GenerativeModel(GEMINI_MODEL)
                    self._model_name = GEMINI_MODEL
                    self._use_new_sdk = False
                    self._configured = True
                    print(f"[Explanation] Gemini configured (legacy SDK): model={GEMINI_MODEL}")
                except Exception as e:
                    print(f"[Explanation] Gemini config failed: {e} — using rule-based fallback")
        else:
            if not _GEMINI_AVAILABLE:
                print("[Explanation] Gemini SDK not installed — using rule-based fallback")
            elif not GEMINI_API_KEY:
                print("[Explanation] GEMINI_API_KEY not set — using rule-based fallback")

    # ── Public API ─────────────────────────────────────────────────────────────

    async def explain(
        self,
        pipeline_output: Dict[str, Any],
        monitoring:      Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a plain-language explanation for a detected fault.

        Args:
            pipeline_output: full pipeline result
            monitoring:      monitoring agent output

        Returns:
            dict with explanation text, or None if below confidence threshold
        """
        rca        = pipeline_output.get("rca_result", {})
        ml         = pipeline_output.get("ml_result", {})
        actual     = pipeline_output.get("actual", {})
        confidence = rca.get("confidence_score", 0.0)

        # Skip if below confidence threshold
        if confidence < MIN_CONFIDENCE:
            return None

        # Build prompt context
        context = {
            "root_cause":    rca.get("root_cause", "Unknown fault"),
            "confidence":    confidence,
            "severity":      rca.get("severity", "MEDIUM"),
            "alert_state":   monitoring.get("alert_state", "ACTIVE"),
            "position":      actual.get("position", 0.0),
            "temperature":   actual.get("temperature", 0.0),
            "pos_error":     pipeline_output.get("pos_error", 0.0),
            "temp_error":    pipeline_output.get("temp_error", 0.0),
            "anomaly_score": ml.get("anomaly_score", 0.0),
            "reasoning_list": "\n".join(
                f"  • {r}" for r in rca.get("reasoning", [])
            ) or "  • No specific conditions logged",
        }

        # Try Gemini first; fall back to rule-based if not available
        if self._configured and self._client:
            result = await self._call_gemini(context)
        else:
            result = self._rule_based_explanation(context)

        self._last_explanation = result
        self._call_count += 1
        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured":        self._configured,
            "model":             GEMINI_MODEL if self._configured else "rule-based-fallback",
            "total_calls":       self._call_count,
            "min_confidence":    MIN_CONFIDENCE,
        }

    # ── Gemini Call ────────────────────────────────────────────────────────────

    async def _call_gemini(self, context: dict) -> dict:
        """Send prompt to Gemini and return structured result."""
        prompt = PROMPT_TEMPLATE.format(**context)

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            if getattr(self, '_use_new_sdk', False):
                # New google.genai SDK
                response = await loop.run_in_executor(
                    None,
                    lambda: self._client.models.generate_content(
                        model=self._model_name,
                        contents=prompt
                    )
                )
                explanation_text = response.text.strip()
            else:
                # Legacy SDK
                response = await loop.run_in_executor(
                    None,
                    lambda: self._client.generate_content(prompt)
                )
                explanation_text = response.text.strip()

            return {
                "explanation":  explanation_text,
                "source":       "gemini",
                "model_used":   GEMINI_MODEL,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "root_cause":   context["root_cause"],
                "confidence":   context["confidence"],
            }
        except Exception as e:
            print(f"[Explanation] Gemini API error: {e} — using fallback")
            return self._rule_based_explanation(context)

    # ── Rule-Based Fallback ────────────────────────────────────────────────────

    def _rule_based_explanation(self, context: Dict) -> Dict[str, Any]:
        """
        Generates a structured explanation without LLM.
        Used when Gemini is not configured or API call fails.
        """
        root_cause = context["root_cause"]
        severity   = context["severity"]
        confidence = context["confidence"]
        reasoning  = context["reasoning_list"]

        # Template-based explanation by fault type
        if "Thermal Runaway" in root_cause:
            para1 = (
                f"The heater subsystem has lost thermal regulation control. "
                f"Temperature is deviating {context['temp_error']:.1f}°C above digital twin predictions, "
                f"indicating the heating element or control loop is no longer responding correctly."
            )
            para2 = "Immediately cut power to the heater element. Do not resume until the SSR/relay and thermocouple connections are physically verified."
            para3 = "Install a hardware thermal fuse as a safety backup. Review PID tuning parameters and add over-temperature software cutoff."

        elif "Mechanical Jam" in root_cause or "Friction" in root_cause:
            para1 = (
                f"The motor is drawing excessive current ({context['pos_error']:.3f}mm position deviation) "
                f"while failing to advance as expected. A mechanical obstruction is resisting movement."
            )
            para2 = "Stop motor immediately to prevent winding damage. Manually inspect lead screw, linear rail, and all coupling points for debris or binding."
            para3 = "Establish a regular lubrication schedule. Consider adding current monitoring with automatic cut-off at 80% of rated current."

        elif "Step Loss" in root_cause or "Calibration" in root_cause:
            para1 = (
                f"The motor is losing positional accuracy — {context['pos_error']:.3f}mm drift from expected position. "
                f"The motor is missing steps or the positional reference has drifted."
            )
            para2 = "Trigger a homing sequence to re-establish position reference. Reduce move velocity by 20% to verify steps are being applied correctly."
            para3 = "Verify motor driver current limit matches motor specs. Consider adding encoder feedback for closed-loop position control."

        elif "Heater" in root_cause:
            para1 = (
                f"The heater element appears to be malfunctioning at normal current draw. "
                f"Temperature deviates {context['temp_error']:.1f}°C from predictions despite motor operating normally."
            )
            para2 = "Check heater cartridge resistance with a multimeter (expected 10–50Ω typically). Inspect wiring crimp connections for loose contacts."
            para3 = "Replace heater cartridge if open-circuit. Log heater cycles to predict future element lifetime."

        elif "Power Supply" in root_cause:
            para1 = (
                "Sudden current spikes without corresponding mechanical movement indicate power supply instability or motor stall conditions."
            )
            para2 = "Measure PSU output voltage under load. Check motor driver bulk capacitors. Verify motor winding resistance is within spec."
            para3 = "Consider upgrading PSU to a unit with better transient response. Add input filter capacitors near the motor driver."

        else:
            para1 = (
                f"The system has deviated from expected behavior with {confidence:.1%} confidence. "
                f"ML anomaly score indicates abnormal operating conditions requiring investigation."
            )
            para2 = "Inspect mechanical and electrical connections. Review recent changes to system configuration or operating conditions."
            para3 = "Monitor system for 30 minutes after inspection. If fault persists, perform full diagnostic sequence."

        explanation = f"{para1}\n\n{para2}\n\n{para3}"

        return {
            "explanation":  explanation,
            "source":       "rule-based-fallback",
            "model_used":   "none",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "root_cause":   root_cause,
            "confidence":   confidence,
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
explanation_agent = ExplanationAgent()
