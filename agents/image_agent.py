from __future__ import annotations

from typing import Any, Dict, List

from Project.services import GeminiService
from Project.utils.validators import validate_url


class ImageQualityAgent:
    """
    Image Quality Agent - Validates product images.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        self.agent_name = "image_quality"

    def analyze(self, product: Dict[str, Any]) -> Dict[str, Any]:
        quick_result = self.quick_check(product)

        # Critical failure: no valid images at all
        if quick_result["score"] == 0:
            return quick_result

        if not self.gemini_service.enabled:
            return quick_result

        images: List[str] = product.get("images") or []
        title = product.get("title", "") or ""
        category = product.get("category", "") or ""

        prompt = (
            "You are evaluating product listing images for an e-commerce platform.\n"
            "Assess whether the number and diversity of images are sufficient, and\n"
            "whether they likely meet quality expectations for the category.\n\n"
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Image URLs ({len(images)}): {images}\n"
        )

        schema = {
            "score": "number 0-100 for overall image quality sufficiency",
            "status": "one of: passed, warning, failed",
            "issues": "list of strings describing issues with images",
            "suggestions": "list of suggestions to improve images",
            "details": {
                "recommended_min_images": "integer",
                "recommended_max_images": "integer",
                "diversity_score": "0-100 estimation of angle/scene diversity",
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

        score = min(float(quick_result["score"]), float(llm_result.get("score", 100.0)))

        status_order = {"failed": 2, "warning": 1, "passed": 0}
        combined_status = (
            quick_result["status"]
            if status_order[quick_result["status"]] >= status_order.get(
                llm_result.get("status", "passed"), 0
            )
            else llm_result.get("status", "passed")
        )

        llm_details = llm_result.get("details", {})
        img_valid_stats = self.validate_image_urls(images)

        return {
            "name": self.agent_name,
            "score": score,
            "status": combined_status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "image_count": len(images),
                "has_images": quick_result["details"]["has_images"],
                "valid_image_urls": img_valid_stats["valid"],
                "invalid_image_urls": img_valid_stats["invalid"],
                "duplicate_urls": img_valid_stats["duplicates"],
                "recommended_min_images": llm_details.get("recommended_min_images", 3),
                "recommended_max_images": llm_details.get("recommended_max_images", 7),
                "diversity_score": llm_details.get("diversity_score", 0),
            },
        }

    def quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        images: List[str] = product.get("images") or []

        issues: List[str] = []
        suggestions: List[str] = []

        if not images:
            issues.append("No product images provided.")
            suggestions.append(
                "Add at least 3 high-quality images showing different angles of the product."
            )
            score = 0.0
            status = "failed"
            has_images = False
        else:
            has_images = True
            count = len(images)
            if count < 3:
                issues.append(f"Only {count} images provided; more are recommended.")
                suggestions.append("Provide at least 3–5 images to build customer trust.")
            elif count > 10:
                issues.append(f"{count} images may be excessive.")
                suggestions.append(
                    "Reduce to the most informative images (ideally 3–7) for better UX."
                )

            stats = self.validate_image_urls(images)
            if stats["invalid"]:
                issues.append("Some image URLs appear invalid.")
                suggestions.append("Fix or replace invalid image URLs.")
            if stats["duplicates"]:
                issues.append("Duplicate image URLs detected.")
                suggestions.append(
                    "Use different images to show the product from multiple perspectives."
                )

            if issues:
                score = 70.0
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
                "image_count": len(images),
                "has_images": has_images,
            },
        }

    def validate_image_urls(self, urls: List[str]) -> Dict[str, Any]:
        valid: List[str] = []
        invalid: List[str] = []
        seen: set[str] = set()
        duplicates: List[str] = []

        for u in urls:
            if u in seen and u not in duplicates:
                duplicates.append(u)
            seen.add(u)
            if validate_url(u):
                valid.append(u)
            else:
                invalid.append(u)

        return {"valid": valid, "invalid": invalid, "duplicates": duplicates}

