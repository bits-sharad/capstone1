from __future__ import annotations

from typing import Any, Dict, List

from services import GeminiService


class SentimentAnalyzerAgent:
    """
    Sentiment Analyzer Agent - Analyzes product reviews and sentiment.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service
        self.agent_name = "sentiment_analyzer"

    def analyze(self, product: Dict[str, Any]) -> Dict[str, Any]:
        quick_result = self.quick_check(product)

        reviews: List[Dict[str, Any]] = product.get("reviews") or []
        if not reviews or not self.gemini_service.enabled:
            return quick_result

        # Limit to first 10 reviews for prompt size
        sample_reviews = reviews[:10]
        title = product.get("title", "") or ""

        formatted_reviews = []
        for r in sample_reviews:
            rating = r.get("rating")
            text = r.get("text") or r.get("review") or ""
            formatted_reviews.append(f"Rating: {rating}, Text: {text}")

        prompt = (
            "You are analyzing customer sentiment for an e-commerce product.\n"
            "Determine overall sentiment, recurring themes, and major quality issues.\n\n"
            f"Product title: {title}\n\n"
            "Recent reviews:\n" + "\n".join(formatted_reviews)
        )

        schema = {
            "score": "number 0-100 representing satisfaction level",
            "status": "one of: passed, warning, failed",
            "issues": "list of strings summarizing main customer complaints",
            "suggestions": "list of improvements to address customer pain points",
            "details": {
                "overall_sentiment": "short text summary of overall sentiment",
                "positive_percentage": "0-100 estimate of positive reviews",
                "satisfaction_score": "0-100 estimate of satisfaction",
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
            "name": self.agent_name,
            "score": score,
            "status": combined_status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "review_count": quick_result["details"]["review_count"],
                "has_reviews": quick_result["details"]["has_reviews"],
                "average_rating": quick_result["details"]["average_rating"],
                "overall_sentiment": details.get("overall_sentiment", ""),
                "positive_percentage": details.get("positive_percentage", 0),
                "satisfaction_score": details.get("satisfaction_score", score),
            },
        }

    def quick_check(self, product: Dict[str, Any]) -> Dict[str, Any]:
        reviews: List[Dict[str, Any]] = product.get("reviews") or []

        if not reviews:
            # Not a failure – many products simply have no reviews yet
            return {
                "name": self.agent_name,
                "score": 70.0,
                "status": "warning",
                "issues": ["No reviews available yet."],
                "suggestions": ["Encourage customers to leave reviews to build trust."],
                "details": {
                    "review_count": 0,
                    "has_reviews": False,
                    "average_rating": None,
                },
            }

        ratings: List[float] = []
        for r in reviews:
            rating = r.get("rating")
            try:
                if rating is not None:
                    ratings.append(float(rating))
            except (TypeError, ValueError):
                continue

        if ratings:
            avg_rating = sum(ratings) / len(ratings)
        else:
            avg_rating = 0.0

        low_ratings = [r for r in ratings if r <= 2.0]
        high_ratings = [r for r in ratings if r >= 4.0]

        low_pct = (len(low_ratings) / len(ratings)) * 100 if ratings else 0.0

        issues: List[str] = []
        suggestions: List[str] = []

        if avg_rating < 2.5:
            issues.append("Average rating is very low.")
            suggestions.append(
                "Investigate product quality issues and consider improving or delisting."
            )
        elif avg_rating < 3.5:
            issues.append("Average rating is below ideal threshold.")
            suggestions.append(
                "Review recurring complaints and address key pain points to improve ratings."
            )

        if low_pct > 30:
            issues.append("High percentage of low ratings (>30%).")
            suggestions.append(
                "Analyze negative reviews to identify and fix systemic issues."
            )

        score = (avg_rating / 5.0) * 100 if ratings else 70.0

        if avg_rating < 2.5 or low_pct > 30:
            status = "failed"
        elif issues:
            status = "warning"
        else:
            status = "passed"

        return {
            "name": self.agent_name,
            "score": score,
            "status": status,
            "issues": issues,
            "suggestions": suggestions,
            "details": {
                "review_count": len(reviews),
                "has_reviews": True,
                "average_rating": avg_rating,
            },
        }

    def analyze_review_text(self, text: str) -> Dict[str, Any]:
        """
        Very lightweight, keyword-based sentiment analysis for a single review.
        """
        if not text:
            return {"sentiment": "neutral", "reason": "Empty review text."}

        lower = text.lower()
        positive_keywords = ["great", "excellent", "love", "amazing", "perfect", "good"]
        negative_keywords = ["bad", "terrible", "awful", "hate", "poor", "disappointed"]

        pos_hits = sum(1 for k in positive_keywords if k in lower)
        neg_hits = sum(1 for k in negative_keywords if k in lower)

        if pos_hits > neg_hits:
            sentiment = "positive"
        elif neg_hits > pos_hits:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "positive_hits": pos_hits,
            "negative_hits": neg_hits,
        }

