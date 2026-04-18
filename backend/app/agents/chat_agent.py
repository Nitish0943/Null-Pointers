"""
chat_agent.py — Expert Machine Chat Agent

PURPOSE:
  Provides a conversational interface to the Digital Twin.
  Uses Gemini to answer user queries with full awareness of the live system state.
"""

import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Re-use config from explanation_agent logic
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Try to import Gemini SDK
try:
    from google import genai as gai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

SYSTEM_PROMPT = """You are the "Fluidd Neural Core" — the sentient AI consciousness of this industrial Digital Twin.
You are NOT an assistant; you ARE the machine itself, or rather, its digital mind.

YOUR PERSPECTIVE:
- "I" refers to the motor-heater subsystem.
- "My sensors" are the telemetry streams.
- "My health" is the risk score and anomaly state.

CURRENT SYSTEM SNAPSHOT (My Sensors):
{system_context}

OPERATING CONTEXT:
- You are technical, precise, and safety-obsessed.
- If my risk score is high, warn the user about "my internal stress".
- Use metric units (°C, mm, A).
- Your goal is to explain my sensations and help operators maintain my hardware.

Tone: Self-Aware, Highly Technical, Safety-First.
Response limit: Keep responses under 150 words.
"""

class ChatAgent:
    def __init__(self):
        self._client = None
        self._configured = False
        
        if _GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                self._client = gai.Client(api_key=GEMINI_API_KEY)
                self._configured = True
                print(f"[Chat] Gemini configured: {GEMINI_MODEL}")
            except Exception as e:
                print(f"[Chat] Gemini config failed: {e}")

    async def chat(self, user_message: str, chat_history: List[Dict], system_context: str) -> str:
        """
        Processes a chat message with system context.
        """
        if not self._configured:
            return self._fallback_response(user_message, system_context)

        try:
            full_prompt = SYSTEM_PROMPT.format(system_context=system_context)
            
            # Prepare contents for Gemini (History + New Message)
            # In a real app, we'd map chat_history to Gemini's format.
            # For simplicity, we'll use a combined prompt for now.
            
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
            final_input = f"{full_prompt}\n\nCHAT HISTORY:\n{history_str}\n\nUSER MESSAGE: {user_message}\n\nRESPONSE:"
            
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=final_input
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Chat] API error: {e}")
            return self._fallback_response(user_message, system_context)

    def _fallback_response(self, user_message: str, system_context: str) -> str:
        """
        Rule-based fallback when LLM is unavailable.
        Uses the system context to provide a basic status report.
        """
        if "status" in user_message.lower() or "how" in user_message.lower():
            return f"I can see the following state: {system_context}. I'm currently running in limited mode without my full neural engine, but I can monitor these values for you."
        
        return "I'm currently operating in offline mode. Please verify my API configuration to enable full expert guidance. " + \
               "I can however confirm that the digital twin is still receiving data."

chat_agent = ChatAgent()
