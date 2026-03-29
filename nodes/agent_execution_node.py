"""
Agent Execution Node - Executes all quality checking agents
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

from Project.state import ProductQualityState, QualityCheckResult
from Project.analyzer.quality_analyzer import QualityAnalyzer


def agent_execution_node(
    state: ProductQualityState, analyzer: Optional[QualityAnalyzer] = None
) -> ProductQualityState:
    state["current_step"] = "agent_execution"  # type: ignore[index]

    # Skip if validation already rejected the product
    if state.get("final_status") == "rejected":
        return state

    if analyzer is None:
        errors = list(state.get("errors", []))
        errors.append("QualityAnalyzer instance is required for agent execution.")
        state["errors"] = errors  # type: ignore[index]
        return state

    product = state.get("product", {})

    try:
        results: List[Dict[str, Any]] = analyzer.run_all_checks(product)
        quality_results: List[QualityCheckResult] = list(
            state.get("quality_results", [])
        )
        quality_results.extend(results)  # type: ignore[arg-type]
        state["quality_results"] = quality_results  # type: ignore[index]

        metadata = state.get("metadata") or {}
        metadata["total_checks"] = len(quality_results)
        state["metadata"] = metadata  # type: ignore[index]
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(f"Error executing agents: {exc}")
        state["errors"] = errors  # type: ignore[index]

    return state

