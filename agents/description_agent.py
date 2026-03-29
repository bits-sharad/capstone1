from __future__ import annotations

from typing import Any, Dict, List

from services import GeminiService


class DescriptionQualityAgent:
    """
    Description Quality Agent - Analyzes product description quality.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        self.agent_name = "description_quality"

    def analyze(self, product: Dict[str, Any]) -> Dict[str, Any]:
        title = product.get("title", "") or ""
        description = product.get("description", "") or ""

        quick_result = self.quick_check(product)

        if not self.gemini_service.enabled:
            return quick_result

        prompt = (
            "You are an expert in e-commerce copywriting.\n"
            "Evaluate the following product title and description for clarity, "
            "completeness, grammar, persuasiveness, keyword usage, and feature coverage.\n\n"
            f"Title: {title}\n\n"
            f"Description:\n{description}\n"
        )

        schema = {
            "score": "number 0-100 for overall description quality",
            "status": "one of: passed, warning, failed",
            "issues": "list of strings describing weaknesses in the description",
            "suggestions": "list of concrete suggestions to improve the copy",
            "details": {
                "clarity_score": "0-100 clarity score",
                "completeness_score": "0-100 completeness score",
                "grammar_score": "0-100 grammar score",
            },
        }

        try:
            llm_result = self.gemini_service.generate_json(prompt, schema)
        except Exception:
            return quick_result

        if not llm_result:
            return quick_result

        llm_result.setdefault("score", quick_result["score"])
        llm_result.setdefault("status", quick_result["status"])
        llm_result.setdefault("issues", [])
        llm_result.setdefault("suggestions", [])
        llm_result.setdefault("details", {})

        issues: List[str] = list(quick_result.get("issues", [])) + list(
            llm_result.get("issues", [])
        )
        suggestions: List[str] = list(quick_result.get("suggestions", [])) + list(
            llm_result.get("suggestions", [])
        )

        status_order = {"failed": 2, "warning": 1, "passed": 0}
        combined_status = (
            quick_result["status"]
            if status_order[quick_result["status"]] >= status_order.get(
                llm_result.get("status", "passed"), 0
            )
            else llm_result.get("status", "passed")
        )

        score = min(float(quick_result["score"]), float(llm_result.get("score", 100.0)))

        details = {
            "title_length": quick_result["details"]["title_length"],
            "description_length": quick_result["details"]["description_length"],
            "clarity_score": llm_result.get("details", {}).get("clarity_score", 0.0),
            "completeness_score": llm_result.get("details", {}).get(
                "completeness_score", 0.0
            ),
            "grammar_score": llm_result.get("details", {}).get("grammar_score", 0.0),
        }

        return {
            "agent_name": self.agent_name,
            "score": score,
            "status": combined_status,
            "issues": issues,
            "suggestions": suggestions,
            "details": details,
        }

    def quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        title = product.get("title", "") or ""
        description = product.get("description", "") or ""

        issues: List[str] = []
        suggestions: List[str] = []

        title_len = len(title.strip())
        desc_len = len(description.strip())

        if not title_len:
            issues.append("Title is missing.")
            suggestions.append("Add a clear, descriptive product title.")
        elif title_len < 10:
            issues.append("Title is very short.")
            suggestions.append("Include key attributes (brand, type, main feature).")
        elif title_len > 200:
            issues.append("Title is too long.")
            suggestions.append("Shorten the title while keeping essential keywords.")

        if not desc_len:
            issues.append("Description is missing.")
            suggestions.append("Provide a detailed description covering key features.")
        elif desc_len < 50:
            issues.append("Description is very short.")
            suggestions.append("Expand the description with features, benefits, and usage.")
        elif desc_len > 5000:
            issues.append("Description is extremely long.")
            suggestions.append("Condense the description to focus on the most important details.")

        if not issues:
            score = 90.0
            status = "passed"
        elif any("missing" in i.lower() for i in issues):
            score = 20.0
            status = "failed"
        else:
            score = 60.0
            status = "warning"

        return {
            "agent_name": self.agent_name,
            "score": score,
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "title_length": title_len,
                "description_length": desc_len,
            },
        }

