"""
State definitions for E-commerce Product Quality Checker.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Dict, List, Optional, TypedDict, Any


class ProductData(TypedDict, total=False):
    """Input product being analyzed."""

    product_id: str
    title: str
    description: str
    price: float
    category: str
    images: List[str]
    specifications: Dict[str, str]
    reviews: Optional[List[Dict[str, str]]]


class QualityCheckResult(TypedDict, total=False):
    """Result from a single quality checking agent."""

    agent_name: str
    status: str  # passed / failed / warning
    score: float  # 0-100
    issues: List[str]
    suggestions: List[str]
    details: Dict[str, Any]


class ProductQualityState(TypedDict, total=False):
    """
    Shared workflow state for LangGraph and the workflow manager.
    """

    product: ProductData
    quality_results: Annotated[List[QualityCheckResult], add]
    overall_score: float
    final_status: str  # approved / rejected / needs_review / pending
    all_issues: Annotated[List[str], add]
    recommendations: Annotated[List[str], add]
    current_step: str
    errors: Annotated[List[str], add]
    metadata: Dict[str, Any]


def create_initial_state(product: ProductData) -> ProductQualityState:
    """
    Construct an initial ProductQualityState for a given product.
    """
    return {
        "product": product,
        "quality_results": [],
        "overall_score": 0.0,
        "final_status": "pending",
        "all_issues": [],
        "recommendations": [],
        "current_step": "initialized",
        "errors": [],
        "metadata": {
            "started_at": None,
            "completed_at": None,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warning_checks": 0,
            "critical_issues_count": 0,
        },
    }
