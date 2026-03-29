"""
Validation Node - Validates input product data
"""

from __future__ import annotations

from datetime import datetime

from state import ProductQualityState, QualityCheckResult
from utils.validators import validate_product_data


def validation_node(state: ProductQualityState) -> ProductQualityState:
    product = state.get("product", {})  # type: ignore[assignment]
    state["current_step"] = "validation"  # type: ignore[index]

    metadata = state.get("metadata") or {}
    if not metadata.get("started_at"):
        metadata["started_at"] = datetime.utcnow().isoformat()
    state["metadata"] = metadata  # type: ignore[index]

    is_valid, validation_errors = validate_product_data(product)

    errors = list(state.get("errors", []))
    quality_results = list(state.get("quality_results", []))

    if not is_valid:
        errors.extend(validation_errors)
        state["errors"] = errors  # type: ignore[index]
        state["final_status"] = "rejected"  # type: ignore[index]

        error_result: QualityCheckResult = {
            "agent_name": "Validation",
            "score": 0.0,
            "status": "failed",
            "issues": validation_errors,
            "suggestions": [
                "Fix validation errors before publishing the product listing."
            ],
            "details": {},
        }
        quality_results.append(error_result)
        state["quality_results"] = quality_results  # type: ignore[index]
        return state

    return state

