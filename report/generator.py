"""
OpsPilot++ Report Generator

Generates comprehensive performance reports for AI agents including:
- Model performance metrics
- Score breakdowns and analysis
- Regret analysis and counterfactual evaluation
- Failure mode detection and categorization
- Detailed explanations and recommendations
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import json
import statistics
from dataclasses import dataclass, asdict


@dataclass
class FailureMode:
    """Represents a detected failure mode."""
    type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    impact: float
    recommendation: str
    examples: List[str]


@dataclass
class PerformanceMetrics:
    """Performance metrics for detailed analysis."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    efficiency: float
    consistency: float


class ReportGenerator:
    """Advanced report generator with comprehensive analysis capabilities."""
    
    def __init__(self):
        self.failure_patterns = {
            "vip_neglect": {
                "keywords": ["vip", "premium", "priority"],
                "severity": "high",
                "description": "Failed to prioritize VIP customer needs"
            },
            "deadline_miss": {
                "keywords": ["deadline", "urgent", "time"],
                "severity": "critical",
                "description": "Missed critical deadlines or time constraints"
            },
            "resource_waste": {
                "keywords": ["energy", "budget", "resource"],
                "severity": "medium",
                "description": "Inefficient resource utilization"
            },
            "poor_scheduling": {
                "keywords": ["schedule", "conflict", "overlap"],
                "severity": "medium",
                "description": "Suboptimal scheduling decisions"
            },
            "communication_gap": {
                "keywords": ["response", "reply", "communication"],
                "severity": "high",
                "description": "Inadequate or inappropriate communication"
            }
        }
    
    def analyze_failure_modes(self, breakdown: Dict[str, Any], explanation: Dict[str, Any]) -> List[FailureMode]:
        """Detect and categorize failure modes from performance data."""
        failures = []
        
        # Analyze score breakdown for negative indicators
        if isinstance(breakdown, dict):
            for category, score in breakdown.items():
                if isinstance(score, (int, float)) and score < 0.5:
                    failure_type = self._categorize_failure(category, explanation)
                    if failure_type:
                        failures.append(failure_type)
        
        # Analyze explanation text for failure patterns
        explanation_text = str(explanation).lower()
        for pattern_name, pattern_info in self.failure_patterns.items():
            if any(keyword in explanation_text for keyword in pattern_info["keywords"]):
                failures.append(FailureMode(
                    type=pattern_name,
                    severity=pattern_info["severity"],
                    description=pattern_info["description"],
                    impact=self._calculate_impact(pattern_name, breakdown),
                    recommendation=self._get_recommendation(pattern_name),
                    examples=self._extract_examples(explanation, pattern_name)
                ))
        
        return failures
    
    def _categorize_failure(self, category: str, explanation: Dict[str, Any]) -> Optional[FailureMode]:
        """Categorize a failure based on category and explanation."""
        category_lower = category.lower()
        
        if "vip" in category_lower or "customer" in category_lower:
            return FailureMode(
                type="customer_service",
                severity="high",
                description=f"Poor performance in {category}",
                impact=0.8,
                recommendation="Focus on customer tier prioritization",
                examples=[f"Low score in {category}"]
            )
        elif "time" in category_lower or "deadline" in category_lower:
            return FailureMode(
                type="time_management",
                severity="critical",
                description=f"Time management issues in {category}",
                impact=0.9,
                recommendation="Improve deadline awareness and scheduling",
                examples=[f"Poor time management in {category}"]
            )
        elif "energy" in category_lower or "resource" in category_lower:
            return FailureMode(
                type="resource_efficiency",
                severity="medium",
                description=f"Resource inefficiency in {category}",
                impact=0.6,
                recommendation="Optimize resource allocation strategies",
                examples=[f"Inefficient resource use in {category}"]
            )
        
        return None
    
    def _calculate_impact(self, failure_type: str, breakdown: Dict[str, Any]) -> float:
        """Calculate the impact score of a failure mode."""
        impact_weights = {
            "vip_neglect": 0.9,
            "deadline_miss": 1.0,
            "resource_waste": 0.6,
            "poor_scheduling": 0.7,
            "communication_gap": 0.8
        }
        return impact_weights.get(failure_type, 0.5)
    
    def _get_recommendation(self, failure_type: str) -> str:
        """Get specific recommendations for failure types."""
        recommendations = {
            "vip_neglect": "Implement VIP customer prioritization rules and escalation procedures",
            "deadline_miss": "Enhance time awareness and implement deadline tracking systems",
            "resource_waste": "Optimize resource allocation algorithms and implement efficiency metrics",
            "poor_scheduling": "Improve scheduling algorithms and conflict detection mechanisms",
            "communication_gap": "Enhance communication protocols and response quality standards"
        }
        return recommendations.get(failure_type, "Review and improve decision-making processes")
    
    def _extract_examples(self, explanation: Dict[str, Any], failure_type: str) -> List[str]:
        """Extract specific examples from explanation data."""
        examples = []
        
        if isinstance(explanation, dict):
            for key, value in explanation.items():
                if isinstance(value, str) and failure_type.replace("_", " ") in value.lower():
                    examples.append(f"{key}: {value}")
        
        return examples[:3]  # Limit to 3 examples
    
    def calculate_performance_metrics(self, breakdown: Dict[str, Any]) -> PerformanceMetrics:
        """Calculate detailed performance metrics from breakdown data."""
        if not isinstance(breakdown, dict):
            return PerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Extract numeric scores
        scores = []
        for value in breakdown.values():
            if isinstance(value, (int, float)):
                scores.append(max(0.0, min(1.0, value)))  # Clamp to [0, 1]
        
        if not scores:
            return PerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Calculate metrics
        accuracy = statistics.mean(scores)
        precision = max(scores) if scores else 0.0
        recall = min(scores) if scores else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        efficiency = accuracy * (1 - statistics.stdev(scores) if len(scores) > 1 else 0)
        consistency = 1 - (statistics.stdev(scores) if len(scores) > 1 else 0)
        
        return PerformanceMetrics(
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1_score, 4),
            efficiency=round(efficiency, 4),
            consistency=round(max(0.0, consistency), 4)
        )
    
    def generate_insights(self, score: float, regret: float, failures: List[Union[FailureMode, Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate actionable insights from performance data."""
        # Convert failures to serializable format for insights
        serializable_failures = []
        for f in failures:
            if isinstance(f, FailureMode):
                serializable_failures.append(asdict(f))
            elif isinstance(f, dict):
                serializable_failures.append(f)
            elif hasattr(f, '__dict__'):
                serializable_failures.append(f.__dict__)
            else:
                serializable_failures.append(str(f))
        
        insights = {
            "overall_assessment": self._assess_overall_performance(score),
            "regret_analysis": self._analyze_regret(regret),
            "critical_issues": [f for f in serializable_failures if f.get('severity') == "critical"],
            "improvement_areas": self._identify_improvement_areas(failures),
            "strengths": self._identify_strengths(score, failures),
            "next_steps": self._generate_next_steps(score, regret, failures)
        }
        
        return insights
    
    def _get_severity(self, failure: Union[FailureMode, Dict[str, Any]]) -> str:
        """Get severity from failure object or dict."""
        if isinstance(failure, FailureMode):
            return failure.severity
        elif isinstance(failure, dict):
            return failure.get('severity', 'medium')
        else:
            return 'medium'
    
    def _get_failure_type(self, failure: Union[FailureMode, Dict[str, Any]]) -> str:
        """Get type from failure object or dict."""
        if isinstance(failure, FailureMode):
            return failure.type
        elif isinstance(failure, dict):
            return failure.get('type', 'unknown')
        else:
            return 'unknown'
    
    def _assess_overall_performance(self, score: float) -> str:
        """Assess overall performance level."""
        if score >= 0.9:
            return "Excellent - Exceptional performance with minimal room for improvement"
        elif score >= 0.8:
            return "Good - Strong performance with some optimization opportunities"
        elif score >= 0.7:
            return "Satisfactory - Adequate performance with clear improvement areas"
        elif score >= 0.6:
            return "Below Average - Significant improvement needed"
        else:
            return "Poor - Major performance issues requiring immediate attention"
    
    def _analyze_regret(self, regret: float) -> Dict[str, Any]:
        """Analyze regret score and provide insights."""
        if regret <= 0.1:
            level = "Low"
            description = "Decisions are close to optimal"
            recommendation = "Maintain current decision-making approach"
        elif regret <= 0.3:
            level = "Moderate"
            description = "Some suboptimal decisions detected"
            recommendation = "Review decision criteria and improve prioritization"
        else:
            level = "High"
            description = "Significant gap from optimal performance"
            recommendation = "Major revision of decision-making strategy needed"
        
        return {
            "level": level,
            "value": regret,
            "description": description,
            "recommendation": recommendation
        }
    
    def _identify_improvement_areas(self, failures: List[Union[FailureMode, Dict[str, Any]]]) -> List[str]:
        """Identify key areas for improvement."""
        areas = []
        failure_types = [self._get_failure_type(f) for f in failures]
        
        if any("vip" in ft or "customer" in ft for ft in failure_types):
            areas.append("Customer relationship management")
        if any("time" in ft or "deadline" in ft for ft in failure_types):
            areas.append("Time management and scheduling")
        if any("resource" in ft or "energy" in ft for ft in failure_types):
            areas.append("Resource optimization")
        if any("communication" in ft for ft in failure_types):
            areas.append("Communication effectiveness")
        
        return areas
    
    def _identify_strengths(self, score: float, failures: List[Union[FailureMode, Dict[str, Any]]]) -> List[str]:
        """Identify performance strengths."""
        strengths = []
        
        if score >= 0.8:
            strengths.append("Overall strong performance")
        
        failure_types = [self._get_failure_type(f) for f in failures]
        if not any("vip" in ft or "customer" in ft for ft in failure_types):
            strengths.append("Good customer service")
        if not any("time" in ft or "deadline" in ft for ft in failure_types):
            strengths.append("Effective time management")
        if not any("resource" in ft for ft in failure_types):
            strengths.append("Efficient resource utilization")
        
        return strengths
    
    def _generate_next_steps(self, score: float, regret: float, failures: List[Union[FailureMode, Dict[str, Any]]]) -> List[str]:
        """Generate actionable next steps."""
        steps = []
        
        # Priority-based recommendations
        critical_failures = [f for f in failures if self._get_severity(f) == "critical"]
        if critical_failures:
            first_critical = critical_failures[0]
            if isinstance(first_critical, FailureMode):
                steps.append(f"Address critical issue: {first_critical.description}")
            elif isinstance(first_critical, dict):
                steps.append(f"Address critical issue: {first_critical.get('description', 'Critical failure detected')}")
        
        if regret > 0.3:
            steps.append("Implement counterfactual learning to reduce decision regret")
        
        if score < 0.7:
            steps.append("Conduct comprehensive performance review and strategy revision")
        
        # Add specific recommendations from failures
        for failure in failures[:2]:  # Top 2 failures
            if isinstance(failure, FailureMode):
                steps.append(failure.recommendation)
            elif isinstance(failure, dict):
                rec = failure.get('recommendation', 'Review and improve performance')
                steps.append(rec)
        
        return steps


def generate_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive performance report.
    
    Args:
        data: Dictionary containing:
            - model: str - Model name
            - score: float - Overall performance score
            - breakdown: dict - Detailed score breakdown
            - regret: float - Regret score from counterfactual analysis
            - explanation: dict - Detailed explanations
            - failure_modes: list (optional) - Pre-identified failure modes
    
    Returns:
        Dictionary containing formatted report with:
        - model: str
        - score: float
        - breakdown: dict
        - regret: float
        - failures: list
        - explanation: dict
        - timestamp: str
        - performance_metrics: dict
        - insights: dict
    """
    generator = ReportGenerator()
    
    # Extract input data with defaults
    model = data.get("model", "Unknown Model")
    score = float(data.get("score", 0.0))
    breakdown = data.get("breakdown", {})
    regret = float(data.get("regret", 0.0))
    explanation = data.get("explanation", {})
    pre_failures = data.get("failure_modes", [])
    
    # Validate inputs
    score = max(0.0, min(1.0, score))
    regret = max(0.0, regret)
    
    # Generate analysis
    detected_failures = generator.analyze_failure_modes(breakdown, explanation)
    all_failures = pre_failures + detected_failures
    
    # Remove duplicates based on type
    unique_failures = []
    seen_types = set()
    for failure in all_failures:
        failure_type = getattr(failure, 'type', str(failure))
        if failure_type not in seen_types:
            unique_failures.append(failure)
            seen_types.add(failure_type)
    
    # Calculate performance metrics
    performance_metrics = generator.calculate_performance_metrics(breakdown)
    
    # Generate insights
    insights = generator.generate_insights(score, regret, unique_failures)
    
    # Create comprehensive report
    report = {
        "model": model,
        "score": round(score, 4),
        "breakdown": breakdown,
        "regret": round(regret, 4),
        "failures": [
            asdict(f) if isinstance(f, FailureMode) else 
            (f if isinstance(f, dict) else f.__dict__ if hasattr(f, '__dict__') else str(f))
            for f in unique_failures
        ],
        "explanation": explanation,
        "timestamp": datetime.now().isoformat(),
        "performance_metrics": asdict(performance_metrics),
        "insights": insights,
        "metadata": {
            "report_version": "1.0.0",
            "generator": "OpsPilot++ Report Generator",
            "total_failures": len(unique_failures),
            "critical_failures": len([f for f in unique_failures if generator._get_severity(f) == 'critical']),
            "performance_grade": _calculate_grade(score),
            "regret_level": insights["regret_analysis"]["level"]
        }
    }
    
    return report


def _calculate_grade(score: float) -> str:
    """Calculate letter grade from score."""
    if score >= 0.95:
        return "A+"
    elif score >= 0.9:
        return "A"
    elif score >= 0.85:
        return "A-"
    elif score >= 0.8:
        return "B+"
    elif score >= 0.75:
        return "B"
    elif score >= 0.7:
        return "B-"
    elif score >= 0.65:
        return "C+"
    elif score >= 0.6:
        return "C"
    elif score >= 0.55:
        return "C-"
    elif score >= 0.5:
        return "D"
    else:
        return "F"


# Utility functions for report formatting and export

def format_report_summary(report: Dict[str, Any]) -> str:
    """Format report as a readable summary."""
    summary = f"""
OpsPilot++ Performance Report
============================

Model: {report['model']}
Overall Score: {report['score']:.3f} ({report['metadata']['performance_grade']})
Regret Level: {report['insights']['regret_analysis']['level']} ({report['regret']:.3f})
Timestamp: {report['timestamp']}

Performance Metrics:
- Accuracy: {report['performance_metrics']['accuracy']:.3f}
- Precision: {report['performance_metrics']['precision']:.3f}
- Recall: {report['performance_metrics']['recall']:.3f}
- F1 Score: {report['performance_metrics']['f1_score']:.3f}
- Efficiency: {report['performance_metrics']['efficiency']:.3f}
- Consistency: {report['performance_metrics']['consistency']:.3f}

Assessment: {report['insights']['overall_assessment']}

Critical Issues: {report['metadata']['critical_failures']}
Total Failures: {report['metadata']['total_failures']}

Next Steps:
"""
    
    for i, step in enumerate(report['insights']['next_steps'], 1):
        summary += f"{i}. {step}\n"
    
    return summary


def export_report_json(report: Dict[str, Any], filename: str) -> bool:
    """Export report to JSON file."""
    try:
        # Create a deep copy and convert all FailureMode objects to dictionaries
        import copy
        serializable_report = copy.deepcopy(report)
        
        # Convert failures to serializable format
        if 'failures' in serializable_report:
            serializable_failures = []
            for failure in serializable_report['failures']:
                if hasattr(failure, '__dict__'):
                    # Convert object to dict
                    failure_dict = {
                        'type': getattr(failure, 'type', 'unknown'),
                        'severity': getattr(failure, 'severity', 'medium'),
                        'description': getattr(failure, 'description', ''),
                        'impact': getattr(failure, 'impact', 0.0),
                        'recommendation': getattr(failure, 'recommendation', ''),
                        'examples': getattr(failure, 'examples', [])
                    }
                    serializable_failures.append(failure_dict)
                else:
                    # Already a dict
                    serializable_failures.append(failure)
            
            serializable_report['failures'] = serializable_failures
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_report, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error exporting report: {e}")
        return False


def compare_reports(report1: Dict[str, Any], report2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two reports and generate improvement analysis."""
    comparison = {
        "score_change": round(report2['score'] - report1['score'], 4),
        "regret_change": round(report2['regret'] - report1['regret'], 4),
        "performance_trend": "improved" if report2['score'] > report1['score'] else "declined",
        "new_failures": len(report2['failures']) - len(report1['failures']),
        "recommendations": []
    }
    
    if comparison["score_change"] > 0:
        comparison["recommendations"].append("Performance is improving - maintain current strategies")
    else:
        comparison["recommendations"].append("Performance declined - review recent changes")
    
    if comparison["regret_change"] < 0:
        comparison["recommendations"].append("Decision quality improved - good progress")
    else:
        comparison["recommendations"].append("Decision regret increased - review decision criteria")
    
    return comparison