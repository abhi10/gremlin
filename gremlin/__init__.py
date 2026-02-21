"""Gremlin - Pre-Ship Risk Critic."""

__version__ = "0.3.0"

# Export main API classes for library usage
from gremlin.api import AnalysisResult, Gremlin, Risk

__all__ = ["Gremlin", "Risk", "AnalysisResult", "__version__"]
