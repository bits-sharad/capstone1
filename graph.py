"""
LangGraph Workflow Definition for E-commerce Quality Checker
"""

from __future__ import annotations

from typing import Any, Dict, Generator

from langgraph.graph import StateGraph, END

from state import ProductQualityState
from nodes import (
    validation_node,
    agent_execution_node,
    aggregation_node,
    decision_node,
)
from analyzer.quality_analyzer import QualityAnalyzer


def create_quality_check_graph(analyzer: QualityAnalyzer):
    """
    Create and compile the LangGraph state machine for the quality check workflow.
    """
    graph = StateGraph(ProductQualityState)

    # Wrapper functions so we can inject the analyzer into the agent execution node
    def validation_step(state: ProductQualityState) -> ProductQualityState:
        return validation_node(state)

    def agent_execution_step(state: ProductQualityState) -> ProductQualityState:
        return agent_execution_node(state, analyzer=analyzer)

    def aggregation_step(state: ProductQualityState) -> ProductQualityState:
        return aggregation_node(state)

    def decision_step(state: ProductQualityState) -> ProductQualityState:
        return decision_node(state)

    # Register nodes
    graph.add_node("validate", validation_step)
    graph.add_node("execute_agents", agent_execution_step)
    graph.add_node("aggregate", aggregation_step)
    graph.add_node("decide", decision_step)

    # Entry point
    graph.set_entry_point("validate")

    # Conditional routing after validation
    def should_execute_agents(state: ProductQualityState) -> str:
        # If validation rejected the product, skip straight to decision
        if state.get("final_status") == "rejected":
            return "decide"
        return "execute_agents"

    graph.add_conditional_edges(
        "validate",
        should_execute_agents,
        {
            "execute_agents": "execute_agents",
            "decide": "decide",
        },
    )

    # Linear flow for remaining steps
    graph.add_edge("execute_agents", "aggregate")
    graph.add_edge("aggregate", "decide")
    graph.add_edge("decide", END)

    return graph.compile()


def visualize_graph(graph, output_file: str) -> None:
    """
    Generate a Mermaid PNG visualization of the workflow graph.
    """
    try:
        mermaid_graph = graph.get_graph()
        mermaid_graph.draw_mermaid_png(output_file)

        # Show inline if running in a Jupyter-like environment
        try:
            from IPython.display import Image, display  # type: ignore

            display(Image(filename=output_file))
        except Exception:
            # It's fine if IPython is not available
            pass
    except ImportError:
        # langgraph visualization extras not installed; fail silently
        pass
    except Exception:
        # Any other visualization error should not break core execution
        pass


def get_workflow_description() -> Dict[str, Any]:
    """
    Return a structured description of the workflow for documentation/UIs.
    """
    return {
        "name": "E-commerce Product Quality Check Workflow",
        "description": (
            "Validates e-commerce product data, runs multiple specialized quality "
            "agents, aggregates their findings, and makes a final approval decision."
        ),
        "steps": [
            {
                "name": "Validate Product",
                "node": "validate",
                "description": "Check required fields and basic product data validity.",
                "agents": ["Validation"],
            },
            {
                "name": "Execute Quality Agents",
                "node": "execute_agents",
                "description": "Run all specialized quality checking agents.",
                "agents": [
                    "DescriptionQualityAgent",
                    "PricingValidatorAgent",
                    "ImageQualityAgent",
                    "CategoryClassifierAgent",
                    "ComplianceCheckerAgent",
                    "SentimentAnalyzerAgent",
                ],
            },
            {
                "name": "Aggregate Results",
                "node": "aggregate",
                "description": "Compute overall score, merge issues and recommendations.",
                "agents": [],
            },
            {
                "name": "Make Final Decision",
                "node": "decide",
                "description": "Determine final status (approved/needs_review/rejected).",
                "agents": [],
            },
        ],
        "flow": "validate -> (execute_agents?) -> aggregate -> decide -> END",
        "conditional_logic": {
            "from": "validate",
            "condition": "If validation rejects product (final_status='rejected'), "
            "skip agent execution and go directly to decision.",
            "branches": {
                "execute_agents": "Run full agent analysis before aggregation and decision.",
                "decide": "Skip agents and aggregate (no-op) then decide.",
            },
        },
    }


class WorkflowExecutor:
    """
    Convenience wrapper around the compiled LangGraph workflow.
    """

    def __init__(self, analyzer: QualityAnalyzer) -> None:
        self.analyzer = analyzer
        self._graph = create_quality_check_graph(analyzer)

    def execute(self, initial_state: ProductQualityState) -> ProductQualityState:
        """
        Run the workflow to completion starting from an initial state.
        """
        try:
            return self._graph.invoke(initial_state)
        except Exception as exc:
            errors = list(initial_state.get("errors", []))
            errors.append(f"Workflow execution error: {exc}")
            initial_state["errors"] = errors  # type: ignore[index]
            initial_state["final_status"] = "rejected"  # type: ignore[index]
            return initial_state

    def stream_execute(
        self, initial_state: ProductQualityState
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream workflow execution, yielding intermediate updates.
        """
        try:
            for update in self._graph.stream(initial_state):
                yield update
        except Exception as exc:
            errors = list(initial_state.get("errors", []))
            errors.append(f"Workflow streaming error: {exc}")
            initial_state["errors"] = errors  # type: ignore[index]
            initial_state["final_status"] = "rejected"  # type: ignore[index]
            yield {"error": True, "state": initial_state}

    def get_graph(self):
        """
        Return the compiled graph instance.
        """
        return self._graph

"""
LangGraph Workflow Definition for E-commerce Quality Checker


TODO: Implementation Tasks
1. Import necessary modules:
   - StateGraph and END from langgraph.graph
   - ProductQualityState from state module
   - All node functions (validation_node, agent_execution_node, aggregation_node, decision_node) from nodes
   - QualityAnalyzer from analyzer


2. Implement create_quality_check_graph() function:
   - Accept analyzer parameter
   - Create StateGraph instance with ProductQualityState type
   - Define wrapper functions for each node (validation_step, agent_execution_step, aggregation_step, decision_step)
   - Add nodes to workflow: "validate", "execute_agents", "aggregate", "decide"
   - Set entry point to "validate" node
   - Define should_execute_agents() conditional function:
     * Returns "decide" if validation failed (final_status='rejected')
     * Returns "execute_agents" otherwise
   - Add conditional edges from validate to either execute_agents or decide
   - Add edge: execute_agents -> aggregate
   - Add edge: aggregate -> decide
   - Add edge: decide -> END
   - Compile and return the graph


3. Implement visualize_graph() function:
   - Accept graph and output_file parameters
   - Generate mermaid PNG visualization using graph.get_graph().draw_mermaid_png()
   - Save visualization to output_file
   - Display in Jupyter if available
   - Handle ImportError and exceptions gracefully


4. Implement get_workflow_description() function:
   - Return dict with workflow metadata:
     * name: "E-commerce Product Quality Check Workflow"
     * description: workflow purpose
     * steps: list of workflow steps with name, description, node, and agents
     * flow: string describing workflow path
     * conditional_logic: dict explaining conditional branches


5. Implement WorkflowExecutor class:
   - __init__ method: Accept analyzer, store it, create graph using create_quality_check_graph()
   - execute() method:
     * Accept initial state
     * Call graph.invoke(state) to run workflow
     * Handle exceptions, add to state['errors'], set final_status='rejected'
     * Return final state
   - stream_execute() method:
     * Accept initial state
     * Yield state updates using graph.stream(state) for real-time progress
     * Handle exceptions and yield error state
   - get_graph() method: Return compiled StateGraph instance
"""



