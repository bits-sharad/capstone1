"""
Report Generator - Generates quality check reports
"""
from typing import Dict, Any
from datetime import datetime
from utils.formatters import (
    format_quality_report,
    format_json_report,
    format_status_badge,
)




class ReportGenerator:
    """Generates reports from quality check results"""


    def __init__(self):
        """Initialize Report Generator"""
        pass


    def generate_text_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate text-based quality report


        Args:
            analysis: Complete analysis results


        Returns:
            Formatted text report
        """
        return format_quality_report(analysis)


    def generate_json_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON-formatted quality report


        Args:
            analysis: Complete analysis results


        Returns:
            JSON report dictionary
        """
        return format_json_report(analysis)


    def generate_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Generate brief summary of quality check


        Args:
            analysis: Complete analysis results


        Returns:
            Summary string
        """
        product = analysis.get('product', {})
        overall_score = analysis.get('overall_score', 0)
        final_status = analysis.get('final_status', 'unknown')
        metadata = analysis.get('metadata', {})


        summary_lines = []
        summary_lines.append(f"Product: {product.get('title', 'Unknown')}")
        summary_lines.append(f"Score: {overall_score:.1f}/100")
        summary_lines.append(f"Status: {format_status_badge(final_status)}")
        summary_lines.append(f"Checks: {metadata.get('passed_checks', 0)} passed, "
                            f"{metadata.get('failed_checks', 0)} failed, "
                            f"{metadata.get('warning_checks', 0)} warnings")


        return "\n".join(summary_lines)


    def generate_executive_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary for decision making


        Args:
            analysis: Complete analysis results


        Returns:
            Executive summary dictionary
        """
        product = analysis.get('product', {})
        overall_score = analysis.get('overall_score', 0)
        final_status = analysis.get('final_status', 'unknown')
        all_issues = analysis.get('all_issues', [])
        recommendations = analysis.get('recommendations', [])
        metadata = analysis.get('metadata', {})


        # Determine recommendation
        if final_status == 'approved':
            recommendation = "APPROVE - Product meets quality standards"
        elif final_status == 'needs_review':
            recommendation = "REVIEW - Product requires improvements before approval"
        else:
            recommendation = "REJECT - Product does not meet minimum quality standards"


        return {
            'product_id': product.get('product_id'),
            'product_title': product.get('title'),
            'overall_score': overall_score,
            'final_status': final_status,
            'recommendation': recommendation,
            'critical_issues_count': metadata.get('critical_issues_count', 0),
            'total_issues_count': len(all_issues),
            'checks_summary': {
                'total': metadata.get('total_checks', 0),
                'passed': metadata.get('passed_checks', 0),
                'failed': metadata.get('failed_checks', 0),
                'warnings': metadata.get('warning_checks', 0)
            },
            'top_issues': all_issues[:5] if all_issues else [],
            'top_recommendations': recommendations[:5] if recommendations else [],
            'timestamp': datetime.now().isoformat()
        }


    def generate_detailed_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed report with all information


        Args:
            analysis: Complete analysis results


        Returns:
            Detailed report dictionary
        """
        return {
            'summary': self.generate_executive_summary(analysis),
            'full_analysis': self.generate_json_report(analysis),
            'text_report': self.generate_text_report(analysis),
            'generated_at': datetime.now().isoformat()
        }


    def generate_agent_report(self, agent_result: Dict[str, Any]) -> str:
        """
        Generate report for a single agent's results


        Args:
            agent_result: Single agent's quality check result


        Returns:
            Formatted agent report
        """
        lines = []
        lines.append(f"Agent: {agent_result.get('agent_name', 'Unknown')}")
        lines.append(f"Score: {agent_result.get('score', 0):.1f}/100")
        lines.append(f"Status: {format_status_badge(agent_result.get('status', 'unknown'))}")


        issues = agent_result.get('issues', [])
        if issues:
            lines.append("\nIssues:")
            for issue in issues:
                lines.append(f"  - {issue}")


        suggestions = agent_result.get('suggestions', [])
        if suggestions:
            lines.append("\nSuggestions:")
            for suggestion in suggestions:
                lines.append(f"  - {suggestion}")


        return "\n".join(lines)


    def generate_comparison_report(
        self,
        analysis1: Dict[str, Any],
        analysis2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comparison report between two analyses


        Args:
            analysis1: First analysis results
            analysis2: Second analysis results


        Returns:
            Comparison report
        """
        return {
            'product1': {
                'id': analysis1.get('product', {}).get('product_id'),
                'title': analysis1.get('product', {}).get('title'),
                'score': analysis1.get('overall_score', 0),
                'status': analysis1.get('final_status', 'unknown')
            },
            'product2': {
                'id': analysis2.get('product', {}).get('product_id'),
                'title': analysis2.get('product', {}).get('title'),
                'score': analysis2.get('overall_score', 0),
                'status': analysis2.get('final_status', 'unknown')
            },
            'comparison': {
                'score_difference': analysis1.get('overall_score', 0) - analysis2.get('overall_score', 0),
                'better_product': 1 if analysis1.get('overall_score', 0) > analysis2.get('overall_score', 0) else 2
            },
            'timestamp': datetime.now().isoformat()
        }



