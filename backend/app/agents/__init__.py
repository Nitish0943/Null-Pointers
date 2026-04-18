"""
agents/__init__.py — Agent package initializer
Exposes the singleton orchestrator for use across the app.
"""
from .orchestrator_agent import orchestrator

__all__ = ["orchestrator"]
