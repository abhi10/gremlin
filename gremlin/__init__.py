"""Gremlin - Exploratory QA Agent."""

__version__ = "0.1.0"

# Export main API classes for library usage
from gremlin.api import AnalysisResult, Gremlin, Risk

__all__ = ["Gremlin", "Risk", "AnalysisResult", "__version__"]
