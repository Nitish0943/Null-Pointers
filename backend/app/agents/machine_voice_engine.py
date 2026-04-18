from typing import Dict, Any, Optional

class MachineVoiceEngine:
    """
    Converts Digital Twin anomalies and technical RCA data into 
    first-person 'human' machine status messages.
    """

    def generate_message(self, ml_result: Dict[str, Any], rca_result: Dict[str, Any]) -> str:
        if not ml_result.get("anomaly", False):
            return "I'm operating normally. All my systems are stable and within design parameters."

        root_cause = rca_result.get("root_cause", "General Anomaly").lower()
        severity = rca_result.get("severity", "LOW").upper()
        
        # Mapping technical faults to human-like 'sensations'
        voice_map = {
            "overheating": [
                "I'm heating up faster than expected! Please check my cooling or reduce my load immediately.",
                "My thermal sensors are reporting a sharp rise. I'm feeling quite hot right now."
            ],
            "thermal": [
                "My temperature is trending above normal levels. I might need a cooldown cycle soon.",
                "I'm detecting a slight fever in my thermal subsystem. Please monitor my environment."
            ],
            "friction": [
                "I'm using more current than normal but moving less. It feels like something is resisting my motion.",
                "I'm detecting significant resistance in my joints. Please check for mechanical obstructions or lubrication needs."
            ],
            "mechanical": [
                "My mechanical feedback is inconsistent. I'm struggling to maintain my exact position.",
                "I'm feeling a bit shaky. My mechanical precision seems to be slipping."
            ],
            "sensor": [
                "My readings feel unstable. I'm having trouble trusting the data from my sensor array.",
                "I'm seeing jitter in my telemetry. Please inspect my sensor wiring and connections."
            ],
            "calibration": [
                "My positional reference feels slightly off. I might need a quick re-calibration to find my zero point again.",
                "I'm sensing a drift in my accuracy. A software update or home-cycle might help me out."
            ]
        }

        # Select message based on root cause keyword matching
        selected_msg = "I'm detecting a deviation in my operation that doesn't feel right. Please check my diagnostics."
        for key, messages in voice_map.items():
            if key in root_cause:
                # Use severity to pick tone (simplified for now: pick first)
                selected_msg = messages[0] if severity in ["HIGH", "CRITICAL"] else messages[1]
                break

        return selected_msg

machine_voice_engine = MachineVoiceEngine()
