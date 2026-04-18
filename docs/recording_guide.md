# Recording Plan & Visual Suggestions

## Hardware Setup
- If using ESP32: Record a side-shot of the motor-heater assembly with a phone.
- If simulated: Show the `scripts/simulate.py` output in a split terminal.

## OBS Screen Layout
- **Slot A**: Main Next.js Dashboard (1920x1080).
- **Slot B**: Backend Terminal (Overlayed small).
- **Slot C**: Browser Inspect / Console (Optional).

## Critical Moments to Capture
1. **The Steady State**: 10 seconds of stable charts.
2. **The "Flash of Red"**: Capture the transition when Anomaly Score exceeds 0.5.
3. **The "Voice" interaction**: Record with audio enabled to capture the TTS voice.
4. **The Admin Panel**: Show the "Savings" counter increasing after a fault.

## Visual Polish (Editing)
- **Callouts**: Use red circles/arrows to point at "Risk Score" during fault.
- **Speed Ramping**: Slow down during the "Root Cause Analysis" rendering.
- **Music**: Technical, futuristic synth-wave (low volume).
