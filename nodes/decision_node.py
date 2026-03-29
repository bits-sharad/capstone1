"""
Decision Node - Makes final quality decision
"""

from __future__ import annotations

from datetime import datetime

from state import ProductQualityState
from utils.helpers import determine_final_status, extract_critical_issues


def decision_node(state: ProductQualityState) -> ProductQualityState:
    state["current_step"] = "decision"  # type: ignore[index]

    # If validation already rejected, keep that as final
    if state.get("final_status") == "rejected":
        return state

    overall_score = float(state.get("overall_score", 0.0))
    quality_results = state.get("quality_results") or {}

    try:
        critical_issues = extract_critical_issues(quality_results)
        final_status = determine_final_status(overall_score, critical_issues)
        state["final_status"] = final_status  # type: ignore[index]

        all_issues = list(state.get("all_issues", []))
        for issue in critical_issues:
            if issue not in all_issues:
                all_issues.append(issue)
        state["all_issues"] = all_issues  # type: ignore[index]

        metadata = state.get("metadata") or {}
        stats = metadata.get("stats") or {}
        stats["critical_issues_count"] = len(critical_issues)
        metadata["stats"] = stats
        metadata["completed_at"] = datetime.utcnow().isoformat()

        # Build a simple decision reason
        if final_status == "approved":
            reason = f"Approved with overall score {overall_score:.1f} and no critical issues."
        elif final_status == "needs_review":
            reason = (
                f"Needs review with overall score {overall_score:.1f} "
                f"and {len(critical_issues)} critical issues."
            )
        else:
            reason = (
                f"Rejected with overall score {overall_score:.1f} "
                f"and {len(critical_issues)} critical issues."
            )
        metadata["decision_reason"] = reason

        state["metadata"] = metadata  # type: ignore[index]
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(f"Error making final decision: {exc}")
        state["errors"] = errors  # type: ignore[index]
        state["final_status"] = "rejected"  # type: ignore[index]

    return state

