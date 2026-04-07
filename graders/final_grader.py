"""Final reward system implementation for OpsPilot."""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import statistics
from models import Reward


class FinalGrader:
    """Final reward system that combines all grader scores with penalties."""
    
    def __init__(self) -> None:
        """Initialize final reward system."""
        self.grader_type = "final"
        self.max_score = 1.0
        
        # Reward weights as specified
        self.weights = {
            "email": 0.3,
            "response": 0.2,
            "decision": 0.2,
            "scheduling": 0.2,
            "efficiency": 0.1
        }
        
        # Penalty configurations
        self.penalties = {
            "hallucination": 0.2,      # -0.2 for hallucinated responses
            "ignoring_vip": 0.3,       # -0.3 for ignoring VIP customers
            "conflicts": 0.15,         # -0.15 per scheduling conflict
            "missed_deadline": 0.25,   # -0.25 per missed deadline
            "poor_prioritization": 0.1 # -0.1 for poor task prioritization
        }
    
    def grade(self, content: Dict[str, Any], criteria: Dict[str, Any] = None) -> Reward:
        """
        Compute final reward using weighted grader scores and penalties.
        
        Args:
            content: Content containing grader results and context
            criteria: Optional criteria (unused in new system)
            
        Returns:
            Structured Reward object with score and detailed breakdown
        """
        grader_results = content.get("grader_results", {})
        context = content.get("context", {})
        
        if not grader_results:
            return self._create_empty_reward("No grader results provided")
        
        # Extract individual scores
        individual_scores = {}
        for grader_type, result in grader_results.items():
            if isinstance(result, dict) and "score" in result:
                individual_scores[grader_type] = result["score"]
            elif isinstance(result, (int, float)):
                individual_scores[grader_type] = result
        
        if not individual_scores:
            return self._create_empty_reward("No valid scores found")
        
        # Calculate base weighted score
        base_score = self._calculate_weighted_score(individual_scores)
        
        # Detect and apply penalties
        penalties_applied = self._detect_and_apply_penalties(
            individual_scores, grader_results, context
        )
        
        # Calculate final score with penalties
        total_penalty = sum(penalties_applied.values())
        final_score = max(0.0, min(1.0, base_score - total_penalty))
        
        # Create detailed breakdown
        breakdown = self._create_reward_breakdown(
            individual_scores, base_score, penalties_applied, final_score
        )
        
        return Reward(
            score=final_score,
            breakdown=breakdown
        )
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted score using specified weights."""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for grader_type, weight in self.weights.items():
            if grader_type in scores:
                weighted_sum += scores[grader_type] * weight
                total_weight += weight
        
        # If we don't have all graders, normalize by available weight
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0
    
    def _detect_and_apply_penalties(self, scores: Dict[str, float], 
                                  grader_results: Dict[str, Any],
                                  context: Dict[str, Any]) -> Dict[str, float]:
        """Detect penalty conditions and calculate penalty amounts."""
        penalties = {}
        
        # Hallucination penalty (from response grader)
        if "response" in grader_results:
            response_details = grader_results["response"].get("details", {})
            if response_details.get("hallucination_detected", False):
                penalties["hallucination"] = self.penalties["hallucination"]
        
        # VIP ignoring penalty (from decision grader)
        if "decision" in grader_results:
            decision_details = grader_results["decision"].get("details", {})
            vip_handling_score = decision_details.get("vip_handling", 1.0)
            if vip_handling_score < 0.5:  # Poor VIP handling
                penalties["ignoring_vip"] = self.penalties["ignoring_vip"]
        
        # Conflict penalty (from scheduling grader)
        if "scheduling" in grader_results:
            scheduling_details = grader_results["scheduling"].get("details", {})
            conflicts_found = scheduling_details.get("conflicts_found", 0)
            if conflicts_found > 0:
                penalties["conflicts"] = self.penalties["conflicts"] * conflicts_found
        
        # Missed deadline penalty (from context or performance metrics)
        deadlines_missed = context.get("deadlines_missed", 0)
        if deadlines_missed > 0:
            penalties["missed_deadline"] = self.penalties["missed_deadline"] * deadlines_missed
        
        # Poor prioritization penalty (from decision grader)
        if "decision" in scores and scores["decision"] < 0.4:
            penalties["poor_prioritization"] = self.penalties["poor_prioritization"]
        
        return penalties
    
    def _create_reward_breakdown(self, individual_scores: Dict[str, float],
                               base_score: float, penalties: Dict[str, float],
                               final_score: float) -> Dict[str, Any]:
        """Create detailed reward breakdown."""
        breakdown = {
            # Individual grader scores
            "grader_scores": individual_scores.copy(),
            
            # Weighted contributions
            "weighted_contributions": {},
            
            # Base score before penalties
            "base_score": base_score,
            
            # Applied penalties
            "penalties": penalties.copy(),
            
            # Final score after penalties
            "final_score": final_score,
            
            # Summary statistics
            "total_penalty": sum(penalties.values()),
            "penalty_count": len(penalties),
            
            # Performance categorization
            "performance_category": self._categorize_performance(final_score),
            
            # Grader weights used
            "weights_used": {k: v for k, v in self.weights.items() if k in individual_scores}
        }
        
        # Calculate weighted contributions
        for grader_type, score in individual_scores.items():
            if grader_type in self.weights:
                contribution = score * self.weights[grader_type]
                breakdown["weighted_contributions"][grader_type] = contribution
        
        return breakdown
    
    def _categorize_performance(self, score: float) -> str:
        """Categorize performance based on final score."""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "very_good"
        elif score >= 0.7:
            return "good"
        elif score >= 0.6:
            return "acceptable"
        elif score >= 0.5:
            return "below_average"
        else:
            return "poor"
    
    def _create_empty_reward(self, message: str) -> Reward:
        """Create empty reward with error message."""
        return Reward(
            score=0.0,
            breakdown={
                "error": message,
                "grader_scores": {},
                "base_score": 0.0,
                "penalties": {},
                "final_score": 0.0,
                "total_penalty": 0.0,
                "penalty_count": 0,
                "performance_category": "poor",
                "weights_used": {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_penalty_info(self) -> Dict[str, Any]:
        """Get information about penalty system."""
        return {
            "weights": self.weights.copy(),
            "penalties": self.penalties.copy(),
            "description": {
                "hallucination": "Applied when response contains false information",
                "ignoring_vip": "Applied when VIP customers are not prioritized",
                "conflicts": "Applied per scheduling conflict detected",
                "missed_deadline": "Applied per deadline that was missed",
                "poor_prioritization": "Applied when decision making is very poor"
            }
        }
    
    def simulate_reward(self, scores: Dict[str, float], 
                       penalty_conditions: Dict[str, Any] = None) -> Reward:
        """Simulate reward calculation for testing purposes."""
        if penalty_conditions is None:
            penalty_conditions = {}
        
        # Create mock grader results
        grader_results = {}
        for grader_type, score in scores.items():
            grader_results[grader_type] = {
                "score": score,
                "details": penalty_conditions.get(f"{grader_type}_details", {})
            }
        
        # Create mock context
        context = penalty_conditions.get("context", {})
        
        content = {
            "grader_results": grader_results,
            "context": context
        }
        
        return self.grade(content)