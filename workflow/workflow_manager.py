"""
Workflow Manager - Manages the quality checking workflow execution
"""

from __future__ import annotations

from typing import Any, Dict

from state import ProductQualityState, create_initial_state
from analyzer.quality_analyzer import QualityAnalyzer
from analyzer.report_generator import ReportGenerator
from nodes import validation_node, aggregation_node, decision_node


class WorkflowManager:
    """
    Coordinates the end-to-end product quality checking workflow.
    """

    def __init__(self, analyzer: QualityAnalyzer) -> None:
        """
        Initialize the workflow manager.

        Args:
            analyzer: Configured QualityAnalyzer instance.
        """
        self.analyzer = analyzer
        self.report_generator = ReportGenerator()

    def execute_workflow(
        self, product: Dict[str, Any], generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the full workflow for a given product.

        Args:
            product: Raw product data to analyze.
            generate_report: Whether to generate report artifacts.

        Returns:
            Dictionary containing final state, analysis, and optional reports.
        """
        state: ProductQualityState = create_initial_state(product)
        state = self._run_workflow(state, self.analyzer)

        analysis: Dict[str, Any] = {
            "product": state.get("product"),
            "quality_results": state.get("quality_results", []),
            "overall_score": state.get("overall_score", 0.0),
            "final_status": state.get("final_status", "pending"),
            "all_issues": state.get("all_issues", []),
            "recommendations": state.get("recommendations", []),
            "metadata": state.get("metadata", {}),
            "errors": state.get("errors", []),
        }

        result: Dict[str, Any] = {"state": state, "analysis": analysis}

        if generate_report:
            reports = {
                "summary": self.report_generator.generate_summary(analysis),
                "executive_summary": self.report_generator.generate_executive_summary(
                    analysis
                ),
                "text_report": self.report_generator.generate_text_report(analysis),
                "json_report": self.report_generator.generate_json_report(analysis),
            }
            result["reports"] = reports

        print(
            f"Workflow completed with status "
            f"{analysis['final_status']} and score {analysis['overall_score']:.1f}"
        )

        return result

    def _run_workflow(
        self, state: ProductQualityState, analyzer: QualityAnalyzer
    ) -> ProductQualityState:
        """
        Internal helper that runs validation, checks, aggregation, and decision steps.
        """
        # Step 1: validation
        try:
            state = validation_node(state)
        except Exception as exc:
            errors = list(state.get("errors", []))
            errors.append(f"Validation error: {exc}")
            state["errors"] = errors  # type: ignore[index]
            state["final_status"] = "rejected"  # type: ignore[index]
            return state

        # Step 2: agent checks (if not already rejected)
        if state.get("final_status") != "rejected":
            try:
                product = state.get("product", {})
                results = analyzer.run_all_checks(product)
                quality_results = list(state.get("quality_results", []))
                quality_results.extend(results)
                state["quality_results"] = quality_results  # type: ignore[index]

                metadata = state.get("metadata") or {}
                metadata["total_checks"] = len(quality_results)
                state["metadata"] = metadata  # type: ignore[index]
            except Exception as exc:
                errors = list(state.get("errors", []))
                errors.append(f"Agent execution error: {exc}")
                state["errors"] = errors  # type: ignore[index]

        # Step 3: aggregation (only if we have results)
        if state.get("quality_results"):
            try:
                state = aggregation_node(state)
            except Exception as exc:
                errors = list(state.get("errors", []))
                errors.append(f"Aggregation error: {exc}")
                state["errors"] = errors  # type: ignore[index]

        # Step 4: final decision
        try:
            state = decision_node(state)
        except Exception as exc:
            errors = list(state.get("errors", []))
            errors.append(f"Decision error: {exc}")
            state["errors"] = errors  # type: ignore[index]
            state["final_status"] = "rejected"  # type: ignore[index]

        return state

    def execute_quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run workflow using only rule-based checks (no LLM).
        """
        quick_analyzer = QualityAnalyzer(
            self.analyzer.gemini_service, use_llm=False
        )
        state: ProductQualityState = create_initial_state(product)
        state = self._run_workflow(state, quick_analyzer)

        analysis: Dict[str, Any] = {
            "product": state.get("product"),
            "quality_results": state.get("quality_results", []),
            "overall_score": state.get("overall_score", 0.0),
            "final_status": state.get("final_status", "pending"),
            "all_issues": state.get("all_issues", []),
            "recommendations": state.get("recommendations", []),
            "metadata": state.get("metadata", {}),
            "errors": state.get("errors", []),
        }

        return {"state": state, "analysis": analysis}

    @staticmethod
    def get_workflow_status(state: ProductQualityState) -> str:
        """
        Return the current workflow step name for a given state.
        """
        return state.get("current_step", "unknown")

    def validate_product_only(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run only the validation step on a product.
        """
        state: ProductQualityState = create_initial_state(product)
        try:
            state = validation_node(state)
        except Exception as exc:
            errors = list(state.get("errors", []))
            errors.append(f"Validation error: {exc}")
            state["errors"] = errors  # type: ignore[index]
            state["final_status"] = "rejected"  # type: ignore[index]

        valid = state.get("final_status") != "rejected"
        return {
            "valid": bool(valid),
            "errors": state.get("errors", []),
            "status": state.get("final_status", "pending"),
        }
