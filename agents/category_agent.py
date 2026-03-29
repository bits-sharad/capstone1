from __future__ import annotations

from typing import Any, Dict, List

from services import GeminiService


VALID_CATEGORIES: List[str] = [
    "Electronics",
    "Computers",
    "Home & Kitchen",
    "Clothing",
    "Books",
    "Health & Personal Care",
    "Sports & Outdoors",
    "Beauty",
    "Toys & Games",
    "Automotive",
]

GENERIC_CATEGORIES = {"Other", "Miscellaneous", "General", "Misc", "Various"}


class CategoryClassifierAgent:
    """
    Category Classifier Agent - Validates product categorization.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        self.agent_name = "category_classifier"

    def analyze(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis entrypoint. Uses Gemini when available and falls back
        to quick, rule-based checks otherwise.
        """
        quick_result = self.quick_check(product)

        if not self.gemini_service.enabled:
            return quick_result

        title = product.get("title", "")
        description = product.get("description", "")
        category = product.get("category", "")
        specs = product.get("specifications") or {}

        prompt = (
            "You are an expert in e-commerce product taxonomy.\n"
            "Evaluate whether the current category is appropriate for this product.\n"
            "Suggest a better category if needed and explain your reasoning.\n\n"
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Current category: {category}\n"
            f"Specifications: {specs}\n"
        )

        schema = {
            "score": "number 0-100 indicating confidence that the category is correct",
            "status": "one of: passed, warning, failed",
            "issues": "list of human readable strings describing problems",
            "suggestions": "list of human readable suggestions for improvement",
            "details": {
                "suggested_category": "string best matching category",
                "reason": "short explanation",
                "is_generic": "boolean, whether the category is overly generic",
            },
        }

        try:
            llm_result = self.gemini_service.generate_json(prompt, schema)
        except Exception:
            return quick_result

        if not llm_result:
            return quick_result

        # Ensure required fields
        llm_result.setdefault("score", quick_result["score"])
        llm_result.setdefault("status", quick_result["status"])
        llm_result.setdefault("issues", [])
        llm_result.setdefault("suggestions", [])
        llm_result.setdefault("details", {})

        issues = list(quick_result.get("issues", [])) + list(llm_result.get("issues", []))
        suggestions = list(quick_result.get("suggestions", [])) + list(
            llm_result.get("suggestions", [])
        )

        # Prefer the lower (more conservative) score
        score = min(float(quick_result["score"]), float(llm_result.get("score", 100.0)))

        # Status escalation: failed > warning > passed
        status_order = {"failed": 2, "warning": 1, "passed": 0}
        combined_status = (
            quick_result["status"]
            if status_order[quick_result["status"]] >= status_order.get(
                llm_result.get("status", "passed"), 0
            )
            else llm_result.get("status", "passed")
        )

        return {
            "name": self.agent_name,
            "score": score,
            "status": combined_status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "current_category": category,
                "suggested_category": llm_result.get("details", {}).get(
                    "suggested_category"
                )
                or quick_result["details"].get("suggested_category"),
                "reason": llm_result.get("details", {}).get("reason", ""),
                "is_generic": quick_result["details"].get("is_generic", False),
            },
        }

    def quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple rule-based validation of category.
        """
        title = product.get("title", "") or ""
        description = product.get("description", "") or ""
        category = (product.get("category") or "").strip()

        issues: List[str] = []
        suggestions: List[str] = []

        if not category:
            issues.append("Category is missing.")
            suggestions.append("Provide a specific category for the product.")
        elif category in GENERIC_CATEGORIES:
            issues.append(f"Category '{category}' is too generic.")
            suggestions.append("Use a more specific category matching the product.")
        elif category not in VALID_CATEGORIES:
            issues.append(f"Category '{category}' is not in the standard taxonomy.")
            suggestions.append("Map the product to the closest valid category.")

        suggested = self.suggest_category(title, description)
        is_generic = category in GENERIC_CATEGORIES

        if issues:
            score = 40.0
            status = "failed"
        else:
            score = 90.0
            status = "passed"

        return {
            "name": self.agent_name,
            "score": score,
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "current_category": category or None,
                "suggested_category": suggested,
                "is_generic": is_generic,
            },
        }

    def suggest_category(self, title: str, description: str) -> str | None:
        """
        Very lightweight keyword-based category suggestion.
        """
        text = f"{title} {description}".lower()

        keyword_map = {
            "Electronics": ["phone", "camera", "tv", "speaker", "headphone"],
            "Computers": ["laptop", "computer", "ssd", "keyboard", "mouse"],
            "Home & Kitchen": ["pan", "kitchen", "sofa", "bedding", "decor"],
            "Clothing": ["shirt", "jeans", "dress", "jacket", "t-shirt"],
            "Books": ["book", "novel", "paperback", "hardcover"],
            "Health & Personal Care": ["supplement", "vitamin", "skincare", "lotion"],
            "Sports & Outdoors": ["tent", "backpack", "yoga", "fitness", "ball"],
            "Beauty": ["makeup", "lipstick", "mascara", "foundation"],
            "Toys & Games": ["toy", "puzzle", "lego", "board game"],
            "Automotive": ["car", "tire", "motor", "engine"],
        }

        for category, keywords in keyword_map.items():
            if any(k in text for k in keywords):
                return category
        return None

