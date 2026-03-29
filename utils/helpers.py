"""
Helper utilities for quality checking
"""
from typing import List, Dict, Any


def _agent_label(result: Dict[str, Any]) -> str:
    """Quality check dicts use ``agent_name``; older code used ``name``."""
    return str(result.get("agent_name") or result.get("name") or "unknown")


def calculate_overall_score(quality_results: List[Dict[str, Any]]) -> float:
    """
    Calculate overall quality score from individual check results


    Args:
        quality_results: List of quality check results


    Returns:
        Overall score (0-100)
    """
    if not quality_results:
        return 0.0


    # Calculate weighted average
    # All agents have equal weight by default
    total_score = sum(result['score'] for result in quality_results)
    overall_score = total_score / len(quality_results)


    return round(overall_score, 2)




def determine_final_status(overall_score: float, critical_failures: List[str] = None) -> str:
    """
    Determine final status based on overall score and critical failures


    Args:
        overall_score: Overall quality score (0-100)
        critical_failures: List of critical failure messages


    Returns:
        Final status: 'approved', 'rejected', or 'needs_review'
    """
    # Check for critical failures first
    if critical_failures and len(critical_failures) > 0:
        return 'rejected'


    # Determine status based on score
    if overall_score >= 80:
        return 'approved'
    elif overall_score >= 60:
        return 'needs_review'
    else:
        return 'rejected'




def merge_issues(quality_results: List[Dict[str, Any]]) -> List[str]:
    """
    Merge all issues from quality check results


    Args:
        quality_results: List of quality check results


    Returns:
        Combined list of all issues
    """
    all_issues = []


    for result in quality_results:
        issues = result.get('issues', [])
        for issue in issues:
            # Prefix with agent name for context
            prefixed_issue = f"[{_agent_label(result)}] {issue}"
            all_issues.append(prefixed_issue)


    return all_issues




def merge_recommendations(quality_results: List[Dict[str, Any]]) -> List[str]:
    """
    Merge all recommendations from quality check results


    Args:
        quality_results: List of quality check results


    Returns:
        Combined list of all recommendations
    """
    all_recommendations = []


    for result in quality_results:
        suggestions = result.get('suggestions', [])
        for suggestion in suggestions:
            # Prefix with agent name for context
            prefixed_suggestion = f"[{_agent_label(result)}] {suggestion}"
            all_recommendations.append(prefixed_suggestion)


    return all_recommendations




def count_check_statuses(quality_results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count the number of checks in each status


    Args:
        quality_results: List of quality check results


    Returns:
        Dictionary with counts for each status
    """
    counts = {
        'passed': 0,
        'failed': 0,
        'warning': 0
    }


    for result in quality_results:
        status = result.get('status', '').lower()
        if status in counts:
            counts[status] += 1


    return counts




def extract_critical_issues(quality_results: List[Dict[str, Any]]) -> List[str]:
    """
    Extract critical issues (from failed checks)


    Args:
        quality_results: List of quality check results


    Returns:
        List of critical issues
    """
    critical_issues = []


    for result in quality_results:
        if result.get('status') == 'failed':
            issues = result.get('issues', [])
            for issue in issues:
                critical_issues.append(f"[CRITICAL - {_agent_label(result)}] {issue}")


    return critical_issues




def calculate_confidence_score(quality_results: List[Dict[str, Any]]) -> float:
    """
    Calculate confidence score based on consistency of results


    Args:
        quality_results: List of quality check results


    Returns:
        Confidence score (0-100)
    """
    if not quality_results:
        return 0.0


    scores = [result['score'] for result in quality_results]


    # Calculate standard deviation
    mean_score = sum(scores) / len(scores)
    variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
    std_dev = variance ** 0.5


    # Higher consistency (lower std dev) = higher confidence
    # Normalize to 0-100 scale
    confidence = max(0, 100 - (std_dev * 2))


    return round(confidence, 2)




def get_agent_summary(quality_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get summary statistics for all agents


    Args:
        quality_results: List of quality check results


    Returns:
        Summary dictionary
    """
    return {
        'total_agents': len(quality_results),
        'status_counts': count_check_statuses(quality_results),
        'average_score': calculate_overall_score(quality_results),
        'confidence': calculate_confidence_score(quality_results),
        'critical_issues_count': len(extract_critical_issues(quality_results))
    }



