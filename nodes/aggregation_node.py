"""
Aggregation Node - Aggregates results from all agents
"""

from __future__ import annotations

from Project.state import ProductQualityState
from Project.utils.helpers import (
    calculate_overall_score,
    merge_issues,
    merge_recommendations,
    count_check_statuses,
)


def aggregation_node(state: ProductQualityState) -> ProductQualityState:
    state["current_step"] = "aggregation"  # type: ignore[index]

    quality_results = state.get("quality_results") or {}
    if not quality_results:
        return state

    try:
        overall = calculate_overall_score(quality_results)
        state["overall_score"] = overall  # type: ignore[index]

        all_issues = merge_issues(quality_results)
        recommendations = merge_recommendations(quality_results)
        state["all_issues"] = all_issues  # type: ignore[index]
        state["recommendations"] = recommendations  # type: ignore[index]

        status_counts = count_check_statuses(quality_results)
        metadata = state.get("metadata") or {}
        stats = metadata.get("stats") or {}
        stats.update(
            {
                "passed_checks": status_counts.get("passed", 0),
                "failed_checks": status_counts.get("failed", 0),
                "warning_checks": status_counts.get("warning", 0),
            }
        )
        metadata["stats"] = stats
        state["metadata"] = metadata  # type: ignore[index]
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(f"Error aggregating results: {exc}")
        state["errors"] = errors  # type: ignore[index]

    return state

