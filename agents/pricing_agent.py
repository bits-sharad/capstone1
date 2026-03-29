from __future__ import annotations

from typing import Any, Dict, List

from services import GeminiService


class PricingValidatorAgent:
    """
    Pricing Validator Agent - Validates product pricing.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        self.agent_name = "pricing_validator"

    def analyze(self, product: Dict[str, Any]) -> Dict[str, Any]:
        quick_result = self.quick_check(product)

        if not self.gemini_service.enabled:
            return quick_result

        price = product.get("price")
        title = product.get("title", "") or ""
        category = product.get("category", "") or ""
        description = product.get("description", "") or ""

        prompt = (
            "You are an expert in pricing for e-commerce.\n"
            "Evaluate whether the price is reasonable and competitive for the product,\n"
            "considering its title, category, and description. Comment on psychological\n"
            "pricing, perceived value, and any risks of being too cheap or too expensive.\n\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Price: {price}\n"
            f"Description:\n{description}\n"
        )

        schema = {
            "score": "number 0-100 for price appropriateness",
            "status": "one of: passed, warning, failed",
            "issues": "list of strings describing pricing issues",
            "suggestions": "list of pricing recommendations",
            "details": {
                "price_reasonableness": "short text summary of price vs expectations",
                "psychological_pricing": "boolean indicating if psychological pricing is used well",
                "competitive_score": "0-100 estimation of competitiveness",
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
        details = llm_result.get("details", {})

        return {
            "agent_name": self.agent_name,
            "score": score,
            "status": combined_status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "price": price,
                "category": category,
                "price_valid": quick_result["details"]["price_valid"],
                "price_reasonableness": details.get("price_reasonableness", ""),
                "psychological_pricing": details.get("psychological_pricing", False),
                "competitive_score": details.get("competitive_score", 0),
            },
        }

    def quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        price = product.get("price")
        category = product.get("category", "") or ""

        issues: List[str] = []
        suggestions: List[str] = []
        price_valid = True

        if price is None:
            issues.append("Price is missing.")
            suggestions.append("Set a numeric price for the product.")
            price_valid = False
        else:
            try:
                value = float(price)
            except (ValueError, TypeError):
                issues.append("Price is not a valid number.")
                suggestions.append("Ensure price is a valid numeric value.")
                price_valid = False
                value = 0.0

            if price_valid:
                if value <= 0:
                    issues.append("Price must be greater than 0.")
                    suggestions.append("Set a positive, non-zero price.")
                    price_valid = False
                if value < 1:
                    issues.append("Extremely low price (< $1).")
                    suggestions.append(
                        "Verify price is correct; very low prices may look suspicious."
                    )
                if value > 100_000:
                    issues.append("Extremely high price (> $100k).")
                    suggestions.append(
                        "Verify that such a high price is intentional and justified."
                    )

                # Psychological pricing (.99 or .95)
                if price_valid:
                    cents = int(round((value - int(value)) * 100))
                    if cents in (99, 95):
                        suggestions.append(
                            "Psychological pricing (.99/.95) is used; this can slightly boost conversions."
                        )

                # Very rough category-based range hints
                cat_lower = category.lower()
                if "electronics" in cat_lower and value < 5:
                    issues.append("Electronics price seems unusually low.")
                if "books" in cat_lower and value > 500:
                    issues.append("Book price seems very high.")

        if not price_valid:
            score = 0.0
            status = "failed"
        elif issues:
            score = 65.0
            status = "warning"
        else:
            score = 95.0
            status = "passed"

        return {
            "agent_name": self.agent_name,
            "score": score,
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "price": price,
                "category": category,
                "price_valid": price_valid,
            },
        }

