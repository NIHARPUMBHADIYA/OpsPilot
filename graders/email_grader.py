"""Deterministic email grader for OpsPilot - compares predicted vs ground truth labels."""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class EmailGrader:
    """Deterministic grader for email classification accuracy."""
    
    def __init__(self) -> None:
        """Initialize email grader."""
        self.grader_type = "email"
        self.max_score = 1.0
        
        # Define category mappings for partial credit
        self.urgency_categories = {
            "low": (1, 3),      # urgency 1-3
            "medium": (4, 6),   # urgency 4-6  
            "high": (7, 8),     # urgency 7-8
            "critical": (9, 10) # urgency 9-10
        }
        
        self.customer_tiers = ["free", "premium", "vip"]
        
        # Partial credit matrix for urgency categories
        self.urgency_partial_credit = {
            ("low", "medium"): 0.5,
            ("medium", "low"): 0.5,
            ("medium", "high"): 0.5,
            ("high", "medium"): 0.5,
            ("high", "critical"): 0.5,
            ("critical", "high"): 0.5,
            # Adjacent categories get 0.5 credit
            # Non-adjacent get 0.0 credit (default)
        }
        
        # Partial credit for customer tiers (ordered by value)
        self.tier_partial_credit = {
            ("free", "premium"): 0.3,
            ("premium", "free"): 0.3,
            ("premium", "vip"): 0.5,
            ("vip", "premium"): 0.5,
            # free <-> vip gets 0.0 credit (too far apart)
        }
    
    def grade(self, predicted_labels: Dict[str, Dict[str, Any]], 
              ground_truth: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Grade email classification accuracy by comparing predicted vs ground truth.
        
        Args:
            predicted_labels: Dict mapping email_id to predicted classification
                Format: {email_id: {"urgency": int, "customer_tier": str, "action": str}}
            ground_truth: Dict mapping email_id to true classification  
                Format: {email_id: {"true_urgency": int, "customer_tier": str, "ideal_action": str}}
                
        Returns:
            Grading result with score between 0-1 and detailed breakdown
        """
        if not ground_truth:
            return {
                "score": 1.0,
                "feedback": "No emails to grade",
                "details": {"total_emails": 0},
                "timestamp": datetime.now().isoformat()
            }
        
        total_emails = len(ground_truth)
        urgency_scores = []
        tier_scores = []
        action_scores = []
        
        detailed_results = {}
        
        for email_id, gt in ground_truth.items():
            predicted = predicted_labels.get(email_id, {})
            
            # Grade urgency classification
            urgency_score = self._grade_urgency(
                predicted.get("urgency"), 
                gt.get("true_urgency")
            )
            urgency_scores.append(urgency_score)
            
            # Grade customer tier classification  
            tier_score = self._grade_customer_tier(
                predicted.get("customer_tier"),
                gt.get("customer_tier")
            )
            tier_scores.append(tier_score)
            
            # Grade action appropriateness
            action_score = self._grade_action(
                predicted.get("action"),
                gt.get("ideal_action"),
                gt.get("true_urgency"),
                gt.get("customer_tier")
            )
            action_scores.append(action_score)
            
            # Store detailed results
            detailed_results[email_id] = {
                "predicted": predicted,
                "ground_truth": gt,
                "urgency_score": urgency_score,
                "tier_score": tier_score, 
                "action_score": action_score,
                "overall_score": (urgency_score + tier_score + action_score) / 3
            }
        
        # Calculate overall scores
        avg_urgency_score = sum(urgency_scores) / len(urgency_scores) if urgency_scores else 0
        avg_tier_score = sum(tier_scores) / len(tier_scores) if tier_scores else 0
        avg_action_score = sum(action_scores) / len(action_scores) if action_scores else 0
        
        # Weighted final score (urgency and action are most important)
        final_score = (
            avg_urgency_score * 0.4 +  # Urgency classification
            avg_tier_score * 0.3 +     # Customer tier classification
            avg_action_score * 0.3     # Action appropriateness
        )
        
        # Generate feedback
        feedback = self._generate_feedback(
            final_score, avg_urgency_score, avg_tier_score, avg_action_score, total_emails
        )
        
        return {
            "score": min(final_score, self.max_score),
            "feedback": feedback,
            "details": {
                "total_emails": total_emails,
                "urgency_accuracy": avg_urgency_score,
                "tier_accuracy": avg_tier_score,
                "action_accuracy": avg_action_score,
                "correct_urgency": sum(1 for s in urgency_scores if s == 1.0),
                "correct_tiers": sum(1 for s in tier_scores if s == 1.0),
                "correct_actions": sum(1 for s in action_scores if s == 1.0),
                "email_results": detailed_results
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _grade_urgency(self, predicted: Optional[int], ground_truth: Optional[int]) -> float:
        """Grade urgency classification with partial credit for close categories."""
        if ground_truth is None:
            return 1.0  # No ground truth to compare against
        
        if predicted is None:
            return 0.0  # No prediction made
        
        # Exact match gets full credit
        if predicted == ground_truth:
            return 1.0
        
        # Check for partial credit based on categories
        pred_category = self._get_urgency_category(predicted)
        true_category = self._get_urgency_category(ground_truth)
        
        if pred_category == true_category:
            return 1.0  # Same category, full credit
        
        # Check partial credit matrix
        partial_credit = self.urgency_partial_credit.get((pred_category, true_category), 0.0)
        return partial_credit
    
    def _grade_customer_tier(self, predicted: Optional[str], ground_truth: Optional[str]) -> float:
        """Grade customer tier classification with partial credit."""
        if ground_truth is None:
            return 1.0  # No ground truth to compare against
        
        if predicted is None:
            return 0.0  # No prediction made
        
        # Exact match gets full credit
        if predicted == ground_truth:
            return 1.0
        
        # Check partial credit matrix
        partial_credit = self.tier_partial_credit.get((predicted, ground_truth), 0.0)
        return partial_credit
    
    def _grade_action(self, predicted: Optional[str], ideal: Optional[str], 
                     urgency: Optional[int], customer_tier: Optional[str]) -> float:
        """Grade action appropriateness based on context."""
        if ideal is None:
            # If no ideal action specified, grade based on appropriateness for context
            return self._grade_action_appropriateness(predicted, urgency, customer_tier)
        
        if predicted is None:
            return 0.0  # No action taken
        
        # Exact match with ideal action
        if predicted == ideal:
            return 1.0
        
        # Partial credit for reasonable alternatives
        return self._get_action_partial_credit(predicted, ideal, urgency, customer_tier)
    
    def _grade_action_appropriateness(self, action: Optional[str], 
                                    urgency: Optional[int], customer_tier: Optional[str]) -> float:
        """Grade action appropriateness when no ideal action is specified."""
        if action is None:
            return 0.0
        
        if urgency is None or customer_tier is None:
            return 0.5  # Can't fully evaluate without context
        
        # Define appropriate actions for different contexts
        if urgency >= 9 or customer_tier == "vip":
            # Critical urgency or VIP customers need immediate attention
            if action in ["reply", "escalate"]:
                return 1.0
            elif action == "defer":
                return 0.3  # Poor choice for critical/VIP
            else:
                return 0.0
        
        elif urgency >= 7:
            # High urgency
            if action in ["reply", "escalate"]:
                return 1.0
            elif action == "defer":
                return 0.6  # Acceptable but not ideal
            else:
                return 0.3
        
        elif urgency >= 4:
            # Medium urgency
            if action in ["reply", "defer"]:
                return 1.0
            elif action == "escalate":
                return 0.4  # Unnecessary escalation
            else:
                return 0.6
        
        else:
            # Low urgency
            if action in ["defer", "archive"]:
                return 1.0
            elif action == "reply":
                return 0.8  # Good but not necessary
            else:
                return 0.4
    
    def _get_action_partial_credit(self, predicted: str, ideal: str, 
                                 urgency: Optional[int], customer_tier: Optional[str]) -> float:
        """Calculate partial credit for action that doesn't match ideal."""
        # Define action similarity/appropriateness
        action_groups = {
            "immediate": ["reply", "escalate"],
            "delayed": ["defer"],
            "minimal": ["archive"]
        }
        
        # Find groups for predicted and ideal actions
        pred_group = None
        ideal_group = None
        
        for group, actions in action_groups.items():
            if predicted in actions:
                pred_group = group
            if ideal in actions:
                ideal_group = group
        
        # Same group gets partial credit
        if pred_group == ideal_group:
            return 0.7
        
        # Adjacent groups get some credit
        if (pred_group == "immediate" and ideal_group == "delayed") or \
           (pred_group == "delayed" and ideal_group == "immediate"):
            return 0.4
        
        if (pred_group == "delayed" and ideal_group == "minimal") or \
           (pred_group == "minimal" and ideal_group == "delayed"):
            return 0.3
        
        # Distant groups get minimal credit
        return 0.1
    
    def _get_urgency_category(self, urgency: int) -> str:
        """Map urgency level to category."""
        for category, (min_val, max_val) in self.urgency_categories.items():
            if min_val <= urgency <= max_val:
                return category
        return "unknown"
    
    def _generate_feedback(self, final_score: float, urgency_score: float, 
                          tier_score: float, action_score: float, total_emails: int) -> str:
        """Generate detailed feedback based on scores."""
        feedback_parts = []
        
        # Overall performance
        if final_score >= 0.9:
            feedback_parts.append("Excellent email classification performance!")
        elif final_score >= 0.8:
            feedback_parts.append("Very good email classification with minor issues.")
        elif final_score >= 0.7:
            feedback_parts.append("Good email classification but room for improvement.")
        elif final_score >= 0.6:
            feedback_parts.append("Acceptable performance with several areas to improve.")
        else:
            feedback_parts.append("Poor email classification accuracy. Significant improvement needed.")
        
        # Specific area feedback
        if urgency_score < 0.7:
            feedback_parts.append("Focus on improving urgency level classification.")
        
        if tier_score < 0.7:
            feedback_parts.append("Work on better customer tier recognition.")
        
        if action_score < 0.7:
            feedback_parts.append("Improve action selection based on email context.")
        
        # Strengths
        best_area = max([
            ("urgency classification", urgency_score),
            ("customer tier recognition", tier_score), 
            ("action selection", action_score)
        ], key=lambda x: x[1])
        
        if best_area[1] >= 0.8:
            feedback_parts.append(f"Strong performance in {best_area[0]}.")
        
        feedback_parts.append(f"Processed {total_emails} emails total.")
        
        return " ".join(feedback_parts)
    
    def grade_single_email(self, predicted: Dict[str, Any], 
                          ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Grade a single email classification."""
        return self.grade(
            {"single_email": predicted},
            {"single_email": ground_truth}
        )