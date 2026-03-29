"""
Main Entry Point for E-commerce Product Quality Checker.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Dict, Tuple

from dotenv import load_dotenv

from services.gemini_service import GeminiService
from analyzer.quality_analyzer import QualityAnalyzer
from workflow.workflow_manager import WorkflowManager
from graph import WorkflowExecutor, get_workflow_description
from state import create_initial_state, ProductData


def load_sample_product() -> ProductData:
    """
    Return a realistic sample product for quick testing.
    """
    return {
        "product_id": "SKU-12345",
        "title": "Wireless Noise-Cancelling Over-Ear Headphones with 30h Battery",
        "description": (
            "Premium wireless over-ear headphones featuring active noise cancellation, "
            "30 hours of battery life, fast USB-C charging, and comfortable memory-foam "
            "ear cushions. Ideal for travel, work, and everyday listening."
        ),
        "price": 149.99,
        "category": "Electronics",
        "images": [
            "https://example.com/images/headphones-front.jpg",
            "https://example.com/images/headphones-side.jpg",
            "https://example.com/images/headphones-folded.jpg",
        ],
        "specifications": {
            "Brand": "Acme Audio",
            "Connectivity": "Bluetooth 5.2",
            "Battery Life": "Up to 30 hours",
            "Charging Port": "USB-C",
            "Color": "Matte Black",
        },
        "reviews": [
            {"rating": 5, "text": "Fantastic sound quality and great noise cancelling."},
            {"rating": 4, "text": "Very comfortable, battery lasts long, good value."},
            {"rating": 2, "text": "Sound is good but my pair had a connectivity issue."},
        ],
    }


def initialize_system(
    api_key: str | None = None, use_llm: bool | None = None
) -> Tuple[GeminiService, QualityAnalyzer, WorkflowManager, bool]:
    """
    Initialize Gemini service, analyzer, and workflow manager.
    """
    load_dotenv()

    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    env_key = os.getenv("GOOGLE_API_KEY")
    if use_llm is None:
        use_llm = bool(env_key)

    if not env_key:
        print("WARNING: GOOGLE_API_KEY not set; running in quick-check (no LLM) mode.")

    try:
        gemini_service = GeminiService()
        analyzer = QualityAnalyzer(gemini_service, use_llm=use_llm)
        workflow_manager = WorkflowManager(analyzer)
        return gemini_service, analyzer, workflow_manager, bool(use_llm)
    except Exception as exc:  # pragma: no cover - fatal initialization
        print(f"Failed to initialize system components: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise


def run_quality_check(
    product: ProductData, workflow_manager: WorkflowManager, show_report: bool = True
) -> Dict[str, Any]:
    """
    Run the full quality check workflow and optionally print a text report.
    """
    result = workflow_manager.execute_workflow(product, generate_report=True)
    if show_report:
        reports = result.get("reports") or {}
        text_report = reports.get("text_report")
        if text_report:
            print("\n=== Quality Check Report ===")
            print(text_report)
    return result


def run_quick_check(
    product: ProductData, workflow_manager: WorkflowManager
) -> Dict[str, Any]:
    """
    Run quick, rule-based checks only.
    """
    result = workflow_manager.execute_quick_check(product)
    analysis = result.get("analysis", {})
    overall = analysis.get("overall_score", 0.0)
    status = analysis.get("final_status", "unknown")
    issues = len(analysis.get("all_issues", []))
    print(
        f"\nQuick check completed: status={status}, "
        f"score={overall:.1f}, issues={issues}"
    )
    return result


def run_with_langgraph(product: ProductData, analyzer: QualityAnalyzer) -> Dict[str, Any]:
    """
    Demonstrate running the same workflow using the LangGraph executor directly.
    """
    executor = WorkflowExecutor(analyzer)
    initial_state = create_initial_state(product)
    final_state = executor.execute(initial_state)

    print(
        "\nLangGraph workflow completed: "
        f"status={final_state.get('final_status', 'unknown')}, "
        f"score={final_state.get('overall_score', 0.0):.1f}"
    )

    return final_state


def main() -> None:
    print("=" * 70)
    print("E-commerce Product Quality Checker")
    print("=" * 70)

    try:
        _, analyzer, workflow_manager, use_llm = initialize_system()

        product = load_sample_product()

        # Show workflow description
        description = get_workflow_description()
        print("\nWorkflow:", description["name"])
        print(description["description"])

        if use_llm:
            result = run_quality_check(product, workflow_manager, show_report=True)
            # Also demonstrate direct LangGraph execution
            run_with_langgraph(product, analyzer)
        else:
            result = run_quick_check(product, workflow_manager)

        analysis = result.get("analysis", {})
        exec_summary = {
            "product_id": analysis.get("product", {}).get("product_id"),
            "overall_score": analysis.get("overall_score", 0.0),
            "final_status": analysis.get("final_status", "unknown"),
            "critical_issues": analysis.get("metadata", {}).get(
                "critical_issues_count", 0
            ),
        }

        print("\n=== Executive Summary ===")
        print(json.dumps(exec_summary, indent=2))

    except Exception:  # pragma: no cover - top-level safety
        print("An unrecoverable error occurred while running the checker.", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
