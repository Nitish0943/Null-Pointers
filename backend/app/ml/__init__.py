"""
__init__.py — ML Package Exports

Exposes the primary inference interface and model trainer
so that other backend modules can import cleanly.
"""

from .inference import predict_anomaly
from .model import train_model

__all__ = ["predict_anomaly", "train_model"]
