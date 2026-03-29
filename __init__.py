"""
E-commerce Product Quality Checker
A multi-agent system for automated product quality verification
"""


__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Multi-agent e-commerce product quality checker using LangGraph and Gemini AI"


from .state import ProductData, ProductQualityState, create_initial_state
from .services import GeminiService
from .analyzer import QualityAnalyzer, ReportGenerator
from .workflow import WorkflowManager


__all__ = [
    'ProductData',
    'ProductQualityState',
    'create_initial_state',
    'GeminiService',
    'QualityAnalyzer',
    'ReportGenerator',
    'WorkflowManager'
]



