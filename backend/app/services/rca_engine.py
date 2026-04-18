"""
rca_engine.py — Root Cause Analysis (RCA) Engine
=================================================

PURPOSE:
  Sits after ML anomaly detection in the pipeline. Takes raw telemetry,
  predicted values, errors, and ML anomaly score as inputs, then applies
  a hybrid rule-based + statistical approach to identify the most probable
  root cause of any detected anomaly.

ARCHITECTURE:
  ┌──────────────────────────────────────────────┐
  │  Telemetry + Errors + ML Score               │
  │           ↓                                  │
  │  [Sliding Window Buffer]                     │
  │           ↓                                  │
  │  [Derived Feature Generator]                 │
  │   • temp_rate_of_change                      │
  │   • position_lag                             │
  │   • current_spike_factor                     │
  │   • movement_efficiency                      │
  │   • reading_consistency                      │
  │           ↓                                  │
  │  [Rule Engine — Ordered Priority]            │
  │   Rule 1: Mechanical Jam / Friction          │
  │   Rule 2: Thermal Runaway                    │
  │   Rule 3: Heater Malfunction                 │
  │   Rule 4: Motor Step Loss / Calibration      │
  │   Rule 5: Power Supply Instability           │
  │   Rule 6: Sensor Fault                       │
  │   Rule 7: Thermal-Mechanical Coupling        │
  │           ↓                                  │
  │  [Confidence Blender]                        │
  │   confidence = 0.7×rule + 0.3×anomaly_score  │
  │           ↓                                  │
  │  {root_cause, confidence, reasoning,         │
  │   recommended_action, contributing_factors}  │
  └──────────────────────────────────────────────┘

USAGE:
  from app.services.rca_engine import rca_engine
  result = rca_engine.analyze(
      actual={"position": ..., "temperature": ..., "current": ...},
      predicted={"position": ..., "temperature": ...},
      pos_error=..., temp_error=..., anomaly_score=..., pwm=...
  )
"""

from collections import deque
from typing import Dict, Any, List
import statistics

# ─── Constants ────────────────────────────────────────────────────────────────

WINDOW_SIZE = 15  # number of recent readings to retain for trend calculations

# Thresholds — tuned for a typical stepper motor + resistive heater subsystem
TEMP_RATE_SPIKE     = 2.5    # °C/step considered rapid heating
TEMP_ERROR_HIGH     = 12.0   # °C deviation from twin = thermal anomaly
TEMP_ERROR_CRITICAL = 20.0   # °C — thermal runaway territory
POS_ERROR_HIGH      = 0.4    # mm — meaningful position drift
POS_ERROR_CRITICAL  = 1.0    # mm — severe position loss
CURRENT_SPIKE_RATIO = 1.8    # if current > 1.8× recent mean → spike
CURRENT_HIGH_ABS    = 3.5    # Amps — high current in absolute terms
CURRENT_NORMAL_MAX  = 2.0    # Amps — threshold for "current is normal"
EFFICIENCY_LOW      = 0.3    # movement per amp — low = friction/jam
NOISE_CV_THRESHOLD  = 0.25   # coefficient of variation above this = noisy sensor


# ─── RCA Result Schema ────────────────────────────────────────────────────────

class RCAResult:
    """Structured output from the RCA engine."""

    def __init__(
        self,
        root_cause: str,
        confidence_score: float,
        reasoning: List[str],
        recommended_action: str,
        contributing_factors: List[str] = None,
        severity: str = "LOW"
    ):
        self.root_cause         = root_cause
        self.confidence_score   = round(confidence_score, 3)
        self.reasoning          = reasoning
        self.recommended_action = recommended_action
        self.contributing_factors = contributing_factors or []
        self.severity           = severity  # LOW | MEDIUM | HIGH | CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_cause":          self.root_cause,
            "confidence_score":    self.confidence_score,
            "severity":            self.severity,
            "reasoning":           self.reasoning,
            "recommended_action":  self.recommended_action,
            "contributing_factors": self.contributing_factors,
        }


# ─── RCA Engine ───────────────────────────────────────────────────────────────

class RCAEngine:
    """
    Hybrid Rule-Based + ML Root Cause Analysis engine.

    Maintains a sliding window of recent telemetry to compute temporal
    features, then dispatches a prioritized rule set to identify the
    most probable fault root cause.
    """

    def __init__(self):
        # Sliding windows for temporal feature derivation
        self._temp_history:    deque = deque(maxlen=WINDOW_SIZE)
        self._pos_history:     deque = deque(maxlen=WINDOW_SIZE)
        self._current_history: deque = deque(maxlen=WINDOW_SIZE)
        self._pos_error_history:  deque = deque(maxlen=WINDOW_SIZE)
        self._temp_error_history: deque = deque(maxlen=WINDOW_SIZE)

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze(
        self,
        actual:       Dict[str, float],
        predicted:    Dict[str, float],
        pos_error:    float,
        temp_error:   float,
        anomaly_score: float,
        pwm:          int = 0,
    ) -> Dict[str, Any]:
        """
        Primary entry point. Call this after ML inference on every telemetry event.

        Args:
            actual:        {"position": float, "temperature": float, "current": float}
            predicted:     {"position": float, "temperature": float}
            pos_error:     |actual_pos  - predicted_pos|  (mm)
            temp_error:    |actual_temp - predicted_temp| (°C)
            anomaly_score: Normalized ML score 0-1 (0=normal, 1=max anomalous)
            pwm:           Current PWM / control signal (0-255)

        Returns:
            RCAResult dict with root_cause, confidence, reasoning, action.
        """
        # Extract raw values
        actual_temp    = actual.get("temperature", 0.0)
        actual_pos     = actual.get("position",    0.0)
        actual_current = actual.get("current",     pwm / 255.0 * 5.0)  # fallback estimate

        # Update sliding windows
        self._temp_history.append(actual_temp)
        self._pos_history.append(actual_pos)
        self._current_history.append(actual_current)
        self._pos_error_history.append(abs(pos_error))
        self._temp_error_history.append(abs(temp_error))

        # Compute derived features
        features = self._derive_features(
            actual_temp, actual_pos, actual_current,
            pos_error, temp_error, pwm
        )

        # Run rules (ordered by priority / severity)
        result = self._dispatch_rules(features, anomaly_score)

        # Attach raw features for transparency
        result["derived_features"] = {k: round(v, 4) for k, v in features.items()}
        return result

    # ── Derived Feature Generator ──────────────────────────────────────────────

    def _derive_features(
        self,
        temp: float, pos: float, current: float,
        pos_error: float, temp_error: float, pwm: int
    ) -> Dict[str, float]:
        """
        Compute temporal and relational features from the sliding window.

        Features derived:
          temp_rate_of_change : rate of temperature increase per reading (°C/step)
          position_lag        : difference between expected and actual movement
          current_spike_factor: current relative to recent average (1.0 = normal)
          movement_efficiency : mm of movement per Amp drawn (low → friction)
          reading_consistency : coefficient of variation of errors (high → noisy sensor)
          temp_error_trend    : whether thermal error is increasing over last N readings
          pos_error_trend     : whether position error is increasing over last N readings
        """
        features: Dict[str, float] = {}

        # 1. Temperature rate of change (°C / reading step)
        if len(self._temp_history) >= 3:
            recent_temps = list(self._temp_history)[-5:]
            features["temp_rate_of_change"] = (recent_temps[-1] - recent_temps[0]) / len(recent_temps)
        else:
            features["temp_rate_of_change"] = 0.0

        # 2. Position lag — how far actual position is from the predicted twin path
        features["position_lag"] = abs(pos_error)

        # 3. Current spike factor — current reading vs. rolling mean
        if len(self._current_history) >= 3:
            mean_current = statistics.mean(list(self._current_history)[:-1]) or 0.001
            features["current_spike_factor"] = current / mean_current
        else:
            features["current_spike_factor"] = 1.0

        # 4. Movement efficiency — mm of position change per Amp
        #    Low efficiency suggests friction, jam, or mechanical overload
        if len(self._pos_history) >= 2:
            pos_change = abs(list(self._pos_history)[-1] - list(self._pos_history)[-2])
        else:
            pos_change = 0.0
        features["movement_efficiency"] = pos_change / (current + 0.01)

        # 5. Reading consistency — coefficient of variation of pos_error signal
        #    Very high CV = erratic readings → potential sensor fault
        if len(self._pos_error_history) >= 5:
            err_values = list(self._pos_error_history)
            mean_err = statistics.mean(err_values) or 0.001
            std_err  = statistics.stdev(err_values)
            features["reading_consistency"] = std_err / mean_err  # CV
        else:
            features["reading_consistency"] = 0.0

        # 6. Absolute error magnitudes (used directly in rules)
        features["abs_temp_error"]    = abs(temp_error)
        features["abs_pos_error"]     = abs(pos_error)
        features["actual_current"]    = current
        features["actual_temp"]       = temp
        features["pwm_normalized"]    = pwm / 255.0

        # 7. Error trend (positive = errors are growing)
        if len(self._pos_error_history) >= 4:
            mid  = len(self._pos_error_history) // 2
            hist = list(self._pos_error_history)
            features["pos_error_trend"] = statistics.mean(hist[mid:]) - statistics.mean(hist[:mid])
        else:
            features["pos_error_trend"] = 0.0

        if len(self._temp_error_history) >= 4:
            mid  = len(self._temp_error_history) // 2
            hist = list(self._temp_error_history)
            features["temp_error_trend"] = statistics.mean(hist[mid:]) - statistics.mean(hist[:mid])
        else:
            features["temp_error_trend"] = 0.0

        return features

    # ── Rule Dispatch Engine ───────────────────────────────────────────────────

    def _dispatch_rules(
        self,
        f: Dict[str, float],
        anomaly_score: float
    ) -> Dict[str, Any]:
        """
        Evaluate all rules and return the highest-confidence RCA result.

        Rules are ordered by priority: critical safety issues first,
        then mechanical, thermal, sensor. Returns the single best match
        plus any additional contributing factors.
        """

        # Run all rules, collect those that triggered
        candidates = []

        candidate = self._rule_mechanical_jam(f, anomaly_score)
        if candidate: candidates.append(candidate)

        candidate = self._rule_thermal_runaway(f, anomaly_score)
        if candidate: candidates.append(candidate)

        candidate = self._rule_heater_malfunction(f, anomaly_score)
        if candidate: candidates.append(candidate)

        candidate = self._rule_motor_step_loss(f, anomaly_score)
        if candidate: candidates.append(candidate)

        candidate = self._rule_power_supply_issue(f, anomaly_score)
        if candidate: candidates.append(candidate)

        candidate = self._rule_sensor_fault(f, anomaly_score)
        if candidate: candidates.append(candidate)

        candidate = self._rule_thermal_mechanical_coupling(f, anomaly_score)
        if candidate: candidates.append(candidate)

        # Sort by confidence descending
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)

        if not candidates:
            # No rules triggered — all nominal
            return RCAResult(
                root_cause         = "No Fault Detected",
                confidence_score   = 1.0 - anomaly_score,
                reasoning          = ["All telemetry within expected bounds"],
                recommended_action = "Continue monitoring. System operating normally.",
                severity           = "LOW"
            ).to_dict()

        # Best match is primary; rest become contributing factors
        primary = candidates[0]
        contributing = [c.root_cause for c in candidates[1:] if c.confidence_score > 0.3]
        primary.contributing_factors = contributing

        return primary.to_dict()

    # ── Rule Definitions ──────────────────────────────────────────────────────
    # Each rule returns an RCAResult if conditions are met, or None if not.

    def _rule_mechanical_jam(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: High current draw + High position error
        CAUSE:   Lead screw jam, excessive friction, foreign object obstruction
        LOGIC:   Motor draws more current trying to move against resistance,
                 but position doesn't advance as expected → large pos_error
        """
        triggered = []
        rule_confidence = 0.0

        if f["actual_current"] > CURRENT_HIGH_ABS:
            triggered.append(f"Current is HIGH ({f['actual_current']:.2f}A > {CURRENT_HIGH_ABS}A threshold)")
            rule_confidence += 0.40

        if f["current_spike_factor"] > CURRENT_SPIKE_RATIO:
            triggered.append(f"Current spike: {f['current_spike_factor']:.2f}× above recent baseline")
            rule_confidence += 0.25

        if f["abs_pos_error"] > POS_ERROR_HIGH:
            triggered.append(f"Position lag: {f['abs_pos_error']:.3f}mm (>{POS_ERROR_HIGH}mm threshold)")
            rule_confidence += 0.25

        if f["movement_efficiency"] < EFFICIENCY_LOW:
            triggered.append(f"Low movement efficiency: {f['movement_efficiency']:.3f} mm/A")
            rule_confidence += 0.10

        if len(triggered) < 2:  # Need at least 2 signals to be confident
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Mechanical Jam or Excessive Friction",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "Immediately reduce motor duty cycle. "
                "Inspect lead screw for debris, lubrication. "
                "Check motor coupling and end-stops."
            ),
            severity = "HIGH" if confidence > 0.7 else "MEDIUM"
        )

    def _rule_thermal_runaway(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: Temperature error CRITICAL + rapid temperature rise
        CAUSE:   Heater stuck ON, thermal control loop failure, coolant failure
        LOGIC:   If temp is rising faster than twin predicts AND the error
                 is in the critical range, the heater is not being regulated.
        """
        triggered = []
        rule_confidence = 0.0

        if f["abs_temp_error"] > TEMP_ERROR_CRITICAL:
            triggered.append(f"Critical thermal deviation: {f['abs_temp_error']:.1f}°C (>{TEMP_ERROR_CRITICAL}°C)")
            rule_confidence += 0.45

        if f["temp_rate_of_change"] > TEMP_RATE_SPIKE:
            triggered.append(f"Temperature rising rapidly: {f['temp_rate_of_change']:.2f}°C/step")
            rule_confidence += 0.35

        if f["temp_error_trend"] > 2.0:
            triggered.append(f"Thermal error trending upward: +{f['temp_error_trend']:.2f}°C/window")
            rule_confidence += 0.20

        if len(triggered) < 2:
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Thermal Runaway — Heater Control Failure",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "EMERGENCY: Cut heater power immediately. "
                "Verify thermal fuse and SSR/relay operation. "
                "Check thermocouple/NTC sensor for short circuit. "
                "Do not resume until control loop is verified."
            ),
            severity = "CRITICAL"
        )

    def _rule_heater_malfunction(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: High temperature error + Normal/Low current
        CAUSE:   Heater element failure (open circuit), loose connections,
                 or wrong heater block installed
        LOGIC:   If temperature is much higher than predicted but the motor
                 current is normal, the issue is in the heater subsystem
                 rather than motor mechanics.
        """
        triggered = []
        rule_confidence = 0.0

        if f["abs_temp_error"] > TEMP_ERROR_HIGH:
            triggered.append(f"High thermal deviation: {f['abs_temp_error']:.1f}°C (>{TEMP_ERROR_HIGH}°C)")
            rule_confidence += 0.50

        if f["actual_current"] < CURRENT_NORMAL_MAX:
            triggered.append(f"Motor current normal: {f['actual_current']:.2f}A (motor not at fault)")
            rule_confidence += 0.30

        # Ensure position is mostly fine (isolates to thermal subsystem)
        if f["abs_pos_error"] < POS_ERROR_HIGH:
            triggered.append(f"Position within bounds: {f['abs_pos_error']:.3f}mm (motor healthy)")
            rule_confidence += 0.20

        if len(triggered) < 2:
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Heater Subsystem Malfunction",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "Inspect heater element continuity with multimeter. "
                "Check wiring terminals and crimp connections. "
                "Verify PID setpoint vs actual PWM duty cycle. "
                "Replace heater cartridge if open-circuit detected."
            ),
            severity = "HIGH" if f["abs_temp_error"] > TEMP_ERROR_CRITICAL else "MEDIUM"
        )

    def _rule_motor_step_loss(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: Position drift + Normal temperature + Normal current
        CAUSE:   Stepper motor missing steps, calibration offset, encoder drift
        LOGIC:   Motor is consuming normal current and temperature is stable,
                 but position is diverging from the digital twin prediction.
                 Classic symptom of step loss or reference drift.
        """
        triggered = []
        rule_confidence = 0.0

        if f["abs_pos_error"] > POS_ERROR_HIGH:
            triggered.append(f"Position drift detected: {f['abs_pos_error']:.3f}mm (>{POS_ERROR_HIGH}mm)")
            rule_confidence += 0.45

        if f["abs_temp_error"] < TEMP_ERROR_HIGH * 0.5:
            triggered.append(f"Temperature stable: {f['abs_temp_error']:.1f}°C deviation (thermal OK)")
            rule_confidence += 0.25

        if f["actual_current"] < CURRENT_HIGH_ABS:
            triggered.append(f"Current normal: {f['actual_current']:.2f}A (no mechanical load)")
            rule_confidence += 0.20

        if f["pos_error_trend"] > 0.05:
            triggered.append(f"Position error trending upward: +{f['pos_error_trend']:.3f}mm/window")
            rule_confidence += 0.10

        if len(triggered) < 2:
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Motor Step Loss or Calibration Drift",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "Perform homing sequence to reset position reference. "
                "Verify microstepping configuration matches firmware. "
                "Check motor driver current limit (torque may be too low). "
                "Inspect belt tension or coupler for slippage."
            ),
            severity = "MEDIUM"
        )

    def _rule_power_supply_issue(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: Current spikes with no corresponding position movement
        CAUSE:   Power supply voltage sag, capacitor failure, motor stall
        LOGIC:   If current jumps abruptly but the motor doesn't move,
                 the energy is being absorbed as heat (stall) or lost to
                 supply instability.
        """
        triggered = []
        rule_confidence = 0.0

        if f["current_spike_factor"] > CURRENT_SPIKE_RATIO:
            triggered.append(f"Sudden current spike: {f['current_spike_factor']:.2f}× baseline")
            rule_confidence += 0.40

        if f["movement_efficiency"] < EFFICIENCY_LOW * 0.5:
            triggered.append(f"Near-zero movement per Amp: {f['movement_efficiency']:.4f} mm/A")
            rule_confidence += 0.35

        if f["abs_pos_error"] < POS_ERROR_HIGH and f["abs_temp_error"] < TEMP_ERROR_HIGH:
            triggered.append("Position and thermal errors are bounded (not mechanical/thermal root)")
            rule_confidence += 0.25

        if len(triggered) < 2:
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Power Supply Instability or Motor Stall",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "Measure PSU rail voltage under load (expect <3% droop). "
                "Check bulk capacitors on motor driver board. "
                "Verify motor winding resistance matches spec. "
                "Consider adding input filter capacitor to PSU."
            ),
            severity = "MEDIUM"
        )

    def _rule_sensor_fault(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: Highly inconsistent/noisy error readings
        CAUSE:   Sensor loose connection, electromagnetic interference, ADC noise,
                 faulty sensor element
        LOGIC:   If the coefficient of variation (CV) of the error signal is very
                 high, the readings are more random than physical — likely a
                 sensor issue rather than a real physical fault.
        """
        triggered = []
        rule_confidence = 0.0

        if f["reading_consistency"] > NOISE_CV_THRESHOLD:
            triggered.append(
                f"High reading noise: CV={f['reading_consistency']:.3f} "
                f"(>{NOISE_CV_THRESHOLD} indicates erratic sensor)"
            )
            rule_confidence += 0.55

        # Contradictory signals are a sensor hallmark
        if f["abs_pos_error"] > POS_ERROR_HIGH and f["actual_current"] < 0.5:
            triggered.append(
                "Contradictory: large position error but near-zero current "
                "(position sensor suspected)"
            )
            rule_confidence += 0.30

        if f["abs_temp_error"] > TEMP_ERROR_HIGH and f["temp_rate_of_change"] < 0:
            triggered.append(
                "Contradictory: large thermal error but temperature actually decreasing "
                "(thermistor/thermocouple suspected)"
            )
            rule_confidence += 0.15

        if rule_confidence < 0.3:
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Sensor Fault or Measurement Noise",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "Check all sensor wiring for loose contacts. "
                "Shield signal cables from high-current motor wires. "
                "Verify sensor calibration coefficient in firmware. "
                "Replace suspect sensor and compare readings."
            ),
            severity = "MEDIUM"
        )

    def _rule_thermal_mechanical_coupling(self, f, anomaly_score) -> RCAResult | None:
        """
        PATTERN: BOTH temperature AND position errors are elevated simultaneously
        CAUSE:   Thermal expansion of mechanical components, lubrication breakdown
                 at high temp, or cascading failure (thermal → mechanical or vice versa)
        LOGIC:   When both error channels are high at the same time, it suggests
                 a coupled failure mode that needs system-level intervention.
        """
        triggered = []
        rule_confidence = 0.0

        if f["abs_temp_error"] > TEMP_ERROR_HIGH:
            triggered.append(f"Elevated thermal error: {f['abs_temp_error']:.1f}°C")
            rule_confidence += 0.35

        if f["abs_pos_error"] > POS_ERROR_HIGH:
            triggered.append(f"Elevated position error: {f['abs_pos_error']:.3f}mm")
            rule_confidence += 0.35

        if f["abs_temp_error"] > TEMP_ERROR_HIGH and f["abs_pos_error"] > POS_ERROR_HIGH:
            triggered.append("Simultaneous multi-channel fault — coupled failure likely")
            rule_confidence += 0.30

        if len(triggered) < 3:  # Requires all three signals
            return None

        confidence = min(1.0, 0.7 * rule_confidence + 0.3 * anomaly_score)
        return RCAResult(
            root_cause         = "Thermal-Mechanical Coupling Failure",
            confidence_score   = confidence,
            reasoning          = triggered,
            recommended_action = (
                "Stop system and allow cool-down before diagnosis. "
                "Inspect linear rail/rod for thermal warping. "
                "Check lubrication — high-temp lubrication may have degraded. "
                "Verify thermal management around motor driver board."
            ),
            severity = "HIGH"
        )


# ─── Singleton instance ───────────────────────────────────────────────────────
# One shared instance so the sliding window persists across requests
rca_engine = RCAEngine()
