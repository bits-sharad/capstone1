from __future__ import annotations

from typing import Any, Dict, List

from Project.services import GeminiService

PROHIBITED_CLAIMS = [
    "cure",
    "miracle",
    "guaranteed results",
    "fda approved",
    "medical grade",
    "treats cancer",
    "permanent cure",
]

REGULATED_CATEGORIES = [
    "Health & Personal Care",
    "Beauty",
    "Medical Devices",
    "Supplements",
    "Alcohol",
    "Tobacco",
    "Adult",
]


class ComplianceCheckerAgent:
    """
    Compliance Checker Agent - Checks regulatory compliance.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        self.agent_name = "compliance_checker"

    def analyze(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run rule-based checks first, then optionally refine with Gemini.
        """
        quick_result = self.quick_check(product)

        if not self.gemini_service.enabled:
            return quick_result

        title = product.get("title", "")
        description = product.get("description", "")
        category = product.get("category", "")

        prompt = (
            "You are an expert in e-commerce regulatory and policy compliance.\n"
            "Analyze this product listing for prohibited claims, required disclosures,\n"
            "age restrictions, safety warnings, and regulatory issues.\n\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Description: {description}\n"
        )

        schema = {
            "score": "number 0-100 (lower when risk is higher)",
            "status": "one of: passed, warning, failed",
            "issues": "list of text descriptions of compliance issues",
            "suggestions": "list of recommendations to resolve issues",
            "details": {
                "prohibited_claims_found": "list of detected problematic phrases",
                "missing_disclosures": "list of missing warnings/age restrictions",
                "risk_level": "one of: low, medium, high, critical",
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

        issues = list(quick_result.get("issues", [])) + list(llm_result.get("issues", []))
        suggestions = list(quick_result.get("suggestions", [])) + list(
            llm_result.get("suggestions", [])
        )

        score = min(float(quick_result["score"]), float(llm_result.get("score", 100.0)))

        status_order = {"failed": 2, "warning": 1, "passed": 0}
        combined_status = (
            quick_result["status"]
            if status_order[quick_result["status"]] >= status_order.get(
                llm_result.get("status", "passed"), 0
            )
            else llm_result.get("status", "passed")
        )

        details = {
            "prohibited_claims_found": list(
                {
                    *quick_result["details"].get("prohibited_claims_found", []),
                    *llm_result.get("details", {}).get("prohibited_claims_found", []),
                }
            ),
            "missing_disclosures": llm_result.get("details", {}).get(
                "missing_disclosures", []
            ),
            "risk_level": llm_result.get("details", {}).get("risk_level", "low"),
        }

        return {
            "name": self.agent_name,
            "score": score,
            "status": combined_status,
            "issues": issues,
            "suggestions": suggestions,
            "details": details,
        }

    def quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        title = (product.get("title") or "").lower()
        description = (product.get("description") or "").lower()
        category = (product.get("category") or "").strip()

        text = f"{title} {description}"

        issues: List[str] = []
        suggestions: List[str] = []
        prohibited_found: List[str] = []

        for claim in PROHIBITED_CLAIMS:
            if claim in text:
                prohibited_found.append(claim)

        if prohibited_found:
            issues.append("Prohibited medical or exaggerated claims detected.")
            suggestions.append(
                "Remove or rephrase medical/exaggerated claims to comply with regulations."
            )

        if category in REGULATED_CATEGORIES:
            issues.append(
                f"Category '{category}' is regulated and may require additional disclosures."
            )
            suggestions.append(
                "Ensure required warnings, certifications, and regulatory statements are present."
            )

        age_issue = self.check_age_restriction(text, category)
        if age_issue:
            issues.append(age_issue)
            suggestions.append("Add clear age restriction and safety warnings.")

        if prohibited_found:
            score = 0.0
            status = "failed"
        elif issues:
            score = 60.0
            status = "warning"
        else:
            score = 95.0
            status = "passed"

        return {
            "name": self.agent_name,
            "score": score,
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "prohibited_claims_found": prohibited_found,
                "regulated_category": category in REGULATED_CATEGORIES,
            },
        }

    def check_age_restriction(self, text: str, category: str) -> str | None:
        keywords = [
            "alcohol",
            "wine",
            "beer",
            "tobacco",
            "cigarette",
            "adult",
            "18+",
            "21+",
        ]
        if any(k in text for k in keywords) or category in {"Alcohol", "Tobacco", "Adult"}:
            if "18" not in text and "21" not in text and "age" not in text:
                return "Potential age-restricted product without explicit age restriction."
        return None

