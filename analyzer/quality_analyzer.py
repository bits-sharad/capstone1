"""
Quality Analyzer - Orchestrates all quality checks
"""
from typing import Dict, Any, List
from services import GeminiService
from agents import (
    DescriptionQualityAgent,
    PricingValidatorAgent,
    ImageQualityAgent,
    CategoryClassifierAgent,
    ComplianceCheckerAgent,
    SentimentAnalyzerAgent
)
from utils.helpers import (
    calculate_overall_score,
    determine_final_status,
    merge_issues,
    merge_recommendations,
    count_check_statuses,
    extract_critical_issues
)




class QualityAnalyzer:
    """Main analyzer that coordinates all quality checking agents"""


    def __init__(self, gemini_service: GeminiService, use_llm: bool = True):
        """
        Initialize Quality Analyzer


        Args:
            gemini_service: Gemini service instance
            use_llm: Whether to use LLM for deep analysis (True) or only quick checks (False)
        """
        self.gemini_service = gemini_service
        self.use_llm = use_llm


        # Initialize all agents
        self.agents = {
            'description': DescriptionQualityAgent(gemini_service),
            'pricing': PricingValidatorAgent(gemini_service),
            'image': ImageQualityAgent(gemini_service),
            'category': CategoryClassifierAgent(gemini_service),
            'compliance': ComplianceCheckerAgent(gemini_service),
            'sentiment': SentimentAnalyzerAgent(gemini_service)
        }


    def run_all_checks(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run all quality checks on a product


        Args:
            product: Product data


        Returns:
            List of quality check results
        """
        results = []


        for agent_name, agent in self.agents.items():
            try:
                if self.use_llm:
                    result = agent.analyze(product)
                else:
                    result = agent.quick_check(product)


                results.append(result)
            except Exception as e:
                # Add error result
                results.append({
                    'agent_name': agent.agent_name,
                    'score': 0.0,
                    'status': 'failed',
                    'issues': [f"Agent execution failed: {str(e)}"],
                    'suggestions': [],
                    'details': {'error': str(e)}
                })


        return results


    def run_specific_checks(
        self,
        product: Dict[str, Any],
        agent_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Run specific quality checks


        Args:
            product: Product data
            agent_names: List of agent names to run


        Returns:
            List of quality check results
        """
        results = []


        for agent_name in agent_names:
            if agent_name not in self.agents:
                results.append({
                    'agent_name': agent_name,
                    'score': 0.0,
                    'status': 'failed',
                    'issues': [f"Unknown agent: {agent_name}"],
                    'suggestions': [],
                    'details': {}
                })
                continue


            agent = self.agents[agent_name]
            try:
                if self.use_llm:
                    result = agent.analyze(product)
                else:
                    result = agent.quick_check(product)


                results.append(result)
            except Exception as e:
                results.append({
                    'agent_name': agent.agent_name,
                    'score': 0.0,
                    'status': 'failed',
                    'issues': [f"Agent execution failed: {str(e)}"],
                    'suggestions': [],
                    'details': {'error': str(e)}
                })


        return results


    def analyze_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete product quality analysis


        Args:
            product: Product data


        Returns:
            Complete analysis results
        """
        # Run all checks
        quality_results = self.run_all_checks(product)


        # Calculate overall score
        overall_score = calculate_overall_score(quality_results)


        # Extract critical issues
        critical_issues = extract_critical_issues(quality_results)


        # Determine final status
        final_status = determine_final_status(overall_score, critical_issues)


        # Merge all issues and recommendations
        all_issues = merge_issues(quality_results)
        recommendations = merge_recommendations(quality_results)


        # Count statuses
        status_counts = count_check_statuses(quality_results)


        # Build complete analysis
        analysis = {
            'product': product,
            'quality_results': quality_results,
            'overall_score': overall_score,
            'final_status': final_status,
            'all_issues': all_issues,
            'recommendations': recommendations,
            'metadata': {
                'total_checks': len(quality_results),
                'passed_checks': status_counts['passed'],
                'failed_checks': status_counts['failed'],
                'warning_checks': status_counts['warning'],
                'critical_issues_count': len(critical_issues),
                'use_llm': self.use_llm
            }
        }


        return analysis


    def get_agent_list(self) -> List[str]:
        """
        Get list of available agents


        Returns:
            List of agent names
        """
        return list(self.agents.keys())


    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """
        Get information about a specific agent


        Args:
            agent_name: Name of the agent


        Returns:
            Agent information
        """
        if agent_name not in self.agents:
            return {'error': f"Agent '{agent_name}' not found"}


        agent = self.agents[agent_name]


        return {
            'name': agent_name,
            'full_name': agent.agent_name,
            'available': True,
            'class': agent.__class__.__name__
        }



