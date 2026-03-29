"""
Formatting utilities for quality reports and outputs
"""
from typing import List, Dict, Any
from datetime import datetime




def format_quality_report(state: Dict[str, Any]) -> str:
    """
    Format quality check results into a readable report


    Args:
        state: Product quality state


    Returns:
        Formatted report string
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PRODUCT QUALITY CHECK REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")


    # Product information
    product = state.get('product', {})
    report_lines.append(f"Product ID: {product.get('product_id', 'N/A')}")
    report_lines.append(f"Title: {product.get('title', 'N/A')}")
    report_lines.append(f"Category: {product.get('category', 'N/A')}")
    report_lines.append(f"Price: ${product.get('price', 0):.2f}")
    report_lines.append("")


    # Overall results
    report_lines.append("-" * 80)
    report_lines.append("OVERALL RESULTS")
    report_lines.append("-" * 80)
    report_lines.append(f"Overall Score: {state.get('overall_score', 0):.1f}/100")
    report_lines.append(f"Final Status: {state.get('final_status', 'unknown').upper()}")
    report_lines.append("")


    # Individual check results
    report_lines.append("-" * 80)
    report_lines.append("INDIVIDUAL CHECKS")
    report_lines.append("-" * 80)


    quality_results = state.get('quality_results', [])
    for result in quality_results:
        report_lines.append(f"\n{result['agent_name']}:")
        report_lines.append(f"  Status: {result['status'].upper()}")
        report_lines.append(f"  Score: {result['score']:.1f}/100")


        if result.get('issues'):
            report_lines.append("  Issues:")
            for issue in result['issues']:
                report_lines.append(f"    - {issue}")


        if result.get('suggestions'):
            report_lines.append("  Suggestions:")
            for suggestion in result['suggestions']:
                report_lines.append(f"    - {suggestion}")


    # All issues summary
    all_issues = state.get('all_issues', [])
    if all_issues:
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("ALL ISSUES SUMMARY")
        report_lines.append("-" * 80)
        for idx, issue in enumerate(all_issues, 1):
            report_lines.append(f"{idx}. {issue}")


    # Recommendations
    recommendations = state.get('recommendations', [])
    if recommendations:
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 80)
        for idx, rec in enumerate(recommendations, 1):
            report_lines.append(f"{idx}. {rec}")


    # Metadata
    metadata = state.get('metadata', {})
    if metadata:
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("METADATA")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Checks: {metadata.get('total_checks', 0)}")
        report_lines.append(f"Passed Checks: {metadata.get('passed_checks', 0)}")
        report_lines.append(f"Failed Checks: {metadata.get('failed_checks', 0)}")


    report_lines.append("")
    report_lines.append("=" * 80)


    return "\n".join(report_lines)




def format_issues(issues: List[str], prefix: str = "- ") -> str:
    """
    Format a list of issues into a readable string


    Args:
        issues: List of issue strings
        prefix: Prefix for each issue


    Returns:
        Formatted issues string
    """
    if not issues:
        return "No issues found"


    return "\n".join([f"{prefix}{issue}" for issue in issues])




def format_json_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format quality check results into a structured JSON report


    Args:
        state: Product quality state


    Returns:
        Structured report dictionary
    """
    return {
        "product": {
            "id": state.get('product', {}).get('product_id'),
            "title": state.get('product', {}).get('title'),
            "category": state.get('product', {}).get('category'),
            "price": state.get('product', {}).get('price')
        },
        "quality_assessment": {
            "overall_score": state.get('overall_score', 0),
            "final_status": state.get('final_status', 'unknown'),
            "timestamp": datetime.now().isoformat()
        },
        "check_results": [
            {
                "agent": result['agent_name'],
                "status": result['status'],
                "score": result['score'],
                "issues": result.get('issues', []),
                "suggestions": result.get('suggestions', [])
            }
            for result in state.get('quality_results', [])
        ],
        "summary": {
            "total_issues": len(state.get('all_issues', [])),
            "issues": state.get('all_issues', []),
            "recommendations": state.get('recommendations', [])
        },
        "metadata": state.get('metadata', {})
    }




def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Format a value as a percentage


    Args:
        value: Value to format (0-100)
        decimal_places: Number of decimal places


    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimal_places}f}%"




def format_status_badge(status: str) -> str:
    """
    Format status with visual badge


    Args:
        status: Status string


    Returns:
        Formatted status with emoji
    """
    badges = {
        'passed': '✓ PASSED',
        'failed': '✗ FAILED',
        'warning': '⚠ WARNING',
        'approved': '✓ APPROVED',
        'rejected': '✗ REJECTED',
        'needs_review': '⚠ NEEDS REVIEW',
        'pending': '⏳ PENDING'
    }


    return badges.get(status.lower(), status.upper())



