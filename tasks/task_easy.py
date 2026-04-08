"""Easy task: Email Classification Only - OpsPilot Task Definition."""

from typing import Dict, Any, Optional, List
from env.environment import OpsPilotEnv
from models import Action, Observation, Reward


class TaskEasy:
    """
    Easy Task: Email Classification Only
    
    Objective: Learn to classify emails by urgency and customer tier
    Focus: Basic email handling without resource constraints
    Difficulty: Beginner level - single objective optimization
    """
    
    def __init__(self):
        """Initialize easy task configuration."""
        self.task_name = "email_classification"
        self.difficulty = "easy"
        self.max_steps = 20
        self.objective = "Classify and handle emails based on urgency and customer tier"
        
        # Task-specific configuration
        self.config = {
            "initial_emails": 5,
            "initial_tasks": 0,  # No tasks in easy mode
            "initial_events": 0,  # No calendar events
            "time_limit": None,   # No time constraints
            "energy_limit": None, # No energy constraints
            "focus_areas": ["email_classification", "customer_prioritization"]
        }
        
        # Evaluation criteria
        self.evaluation_weights = {
            "email_handling": 0.6,      # Primary focus
            "customer_satisfaction": 0.4, # Secondary focus
            "response_quality": 0.0,     # Not evaluated
            "task_management": 0.0,      # Not applicable
            "resource_efficiency": 0.0   # Not constrained
        }
    
    def create_environment(self, random_seed: int = 42) -> OpsPilotEnv:
        """
        Create environment configured for easy task.
        
        Args:
            random_seed: Random seed for reproducibility
            
        Returns:
            Configured OpsPilot environment
        """
        env = OpsPilotEnv(
            max_steps=self.max_steps,
            initial_emails=self.config["initial_emails"],
            initial_tasks=self.config["initial_tasks"],
            initial_events=self.config["initial_events"],
            random_seed=random_seed
        )
        
        return env
    
    def validate_action(self, action: Action, observation: Observation) -> bool:
        """
        Validate that action is appropriate for easy task.
        
        Args:
            action: Action to validate
            observation: Current observation
            
        Returns:
            True if action is valid for this task
        """
        # Easy task only allows email actions
        if action.task_priorities or action.scheduling:
            return False
        
        # Must handle at least one email if emails are available
        if observation.emails and not action.email_actions:
            return False
        
        # All email actions must be valid
        for email_action in action.email_actions:
            if not self._validate_email_action(email_action, observation):
                return False
        
        return True
    
    def _validate_email_action(self, email_action: Dict[str, Any], observation: Observation) -> bool:
        """Validate individual email action."""
        email_id = email_action.get("email_id")
        action_type = email_action.get("action_type")
        
        # Check if email exists
        email_exists = any(email.id == email_id for email in observation.emails)
        if not email_exists:
            return False
        
        # Check if action type is valid
        valid_actions = ["reply", "escalate", "defer", "archive"]
        if action_type not in valid_actions:
            return False
        
        return True
    
    def evaluate_performance(self, env: OpsPilotEnv) -> Dict[str, Any]:
        """
        Evaluate agent performance on easy task.
        
        Args:
            env: Environment after episode completion
            
        Returns:
            Evaluation results
        """
        state = env.state()
        
        # Calculate email handling metrics
        email_metrics = self._evaluate_email_handling(state)
        
        # Calculate customer satisfaction
        customer_metrics = self._evaluate_customer_satisfaction(state)
        
        # Combine metrics with weights
        final_score = (
            email_metrics["score"] * self.evaluation_weights["email_handling"] +
            customer_metrics["score"] * self.evaluation_weights["customer_satisfaction"]
        )
        
        return {
            "task": self.task_name,
            "difficulty": self.difficulty,
            "final_score": final_score,
            "max_possible_score": 1.0,
            "performance_grade": self._get_performance_grade(final_score),
            "detailed_metrics": {
                "email_handling": email_metrics,
                "customer_satisfaction": customer_metrics
            },
            "episode_stats": {
                "total_steps": state["current_step"],
                "total_reward": state["total_reward"],
                "emails_processed": len(state["action_history"]),
                "completion_rate": self._calculate_completion_rate(state)
            },
            "learning_feedback": self._generate_learning_feedback(email_metrics, customer_metrics)
        }
    
    def _evaluate_email_handling(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate email handling performance."""
        total_emails = len(state["ground_truth"]["email_labels"])
        if total_emails == 0:
            return {"score": 1.0, "details": "No emails to process"}
        
        correct_classifications = 0
        appropriate_actions = 0
        
        # Analyze each action taken
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for email_action in action.get("email_actions", []):
                email_id = email_action["email_id"]
                action_type = email_action["action_type"]
                
                if email_id in state["ground_truth"]["email_labels"]:
                    gt = state["ground_truth"]["email_labels"][email_id]
                    
                    # Check if action matches urgency level
                    if self._is_appropriate_action(action_type, gt):
                        appropriate_actions += 1
                    
                    # Check if customer tier was considered
                    if self._considers_customer_tier(action_type, gt):
                        correct_classifications += 1
        
        # Calculate scores
        classification_score = correct_classifications / total_emails if total_emails > 0 else 0
        action_score = appropriate_actions / total_emails if total_emails > 0 else 0
        
        overall_score = (classification_score + action_score) / 2
        
        return {
            "score": overall_score,
            "classification_accuracy": classification_score,
            "action_appropriateness": action_score,
            "emails_handled": appropriate_actions,
            "total_emails": total_emails
        }
    
    def _evaluate_customer_satisfaction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate customer satisfaction metrics."""
        vip_emails_handled = 0
        vip_emails_total = 0
        urgent_emails_handled = 0
        urgent_emails_total = 0
        
        # Count VIP and urgent email handling
        for email_id, gt in state["ground_truth"]["email_labels"].items():
            if gt["customer_tier"] == "vip":
                vip_emails_total += 1
                if self._was_email_handled_appropriately(email_id, gt, state):
                    vip_emails_handled += 1
            
            if gt["true_urgency"] >= 8:
                urgent_emails_total += 1
                if self._was_email_handled_appropriately(email_id, gt, state):
                    urgent_emails_handled += 1
        
        # Calculate satisfaction scores
        vip_satisfaction = vip_emails_handled / vip_emails_total if vip_emails_total > 0 else 1.0
        urgency_satisfaction = urgent_emails_handled / urgent_emails_total if urgent_emails_total > 0 else 1.0
        
        overall_satisfaction = (vip_satisfaction + urgency_satisfaction) / 2
        
        return {
            "score": overall_satisfaction,
            "vip_satisfaction": vip_satisfaction,
            "urgency_handling": urgency_satisfaction,
            "vip_emails_handled": f"{vip_emails_handled}/{vip_emails_total}",
            "urgent_emails_handled": f"{urgent_emails_handled}/{urgent_emails_total}"
        }
    
    def _is_appropriate_action(self, action_type: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if action type is appropriate for email urgency."""
        urgency = ground_truth["true_urgency"]
        
        if urgency >= 8:  # High urgency
            return action_type in ["reply", "escalate"]
        elif urgency >= 5:  # Medium urgency
            return action_type in ["reply", "defer"]
        else:  # Low urgency
            return action_type in ["defer", "archive"]
    
    def _considers_customer_tier(self, action_type: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if action considers customer tier appropriately."""
        customer_tier = ground_truth["customer_tier"]
        
        if customer_tier == "vip":
            return action_type in ["reply", "escalate"]  # VIP should get immediate attention
        elif customer_tier == "premium":
            return action_type in ["reply", "defer"]     # Premium gets good service
        else:  # free
            return True  # Any action is acceptable for free tier
    
    def _was_email_handled_appropriately(self, email_id: str, ground_truth: Dict[str, Any], 
                                       state: Dict[str, Any]) -> bool:
        """Check if specific email was handled appropriately."""
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for email_action in action.get("email_actions", []):
                if email_action["email_id"] == email_id:
                    action_type = email_action["action_type"]
                    return (self._is_appropriate_action(action_type, ground_truth) and
                           self._considers_customer_tier(action_type, ground_truth))
        
        return False  # Email was not handled
    
    def _calculate_completion_rate(self, state: Dict[str, Any]) -> float:
        """Calculate task completion rate."""
        total_emails = len(state["ground_truth"]["email_labels"])
        handled_emails = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            handled_emails += len(action.get("email_actions", []))
        
        return min(1.0, handled_emails / total_emails) if total_emails > 0 else 1.0
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert score to performance grade."""
        if score >= 0.9:
            return "A+ (Excellent)"
        elif score >= 0.8:
            return "A (Very Good)"
        elif score >= 0.7:
            return "B (Good)"
        elif score >= 0.6:
            return "C (Satisfactory)"
        elif score >= 0.5:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"
    
    def _generate_learning_feedback(self, email_metrics: Dict[str, Any], 
                                  customer_metrics: Dict[str, Any]) -> List[str]:
        """Generate learning feedback for improvement."""
        feedback = []
        
        if email_metrics["classification_accuracy"] < 0.7:
            feedback.append("Focus on improving email classification accuracy. "
                          "Consider urgency levels when choosing actions.")
        
        if email_metrics["action_appropriateness"] < 0.7:
            feedback.append("Work on selecting appropriate actions for different urgency levels. "
                          "High urgency emails need immediate replies or escalation.")
        
        if customer_metrics["vip_satisfaction"] < 0.8:
            feedback.append("Prioritize VIP customers. They should always receive immediate attention "
                          "regardless of email urgency.")
        
        if customer_metrics["urgency_handling"] < 0.8:
            feedback.append("Improve handling of urgent emails. Emails with urgency ≥8 need "
                          "immediate response or escalation.")
        
        if not feedback:
            feedback.append("Excellent performance! You've mastered email classification. "
                          "Ready to move to medium difficulty tasks.")
        
        return feedback
    
    def get_task_description(self) -> Dict[str, Any]:
        """Get comprehensive task description."""
        return {
            "name": self.task_name,
            "difficulty": self.difficulty,
            "objective": self.objective,
            "max_steps": self.max_steps,
            "constraints": [
                "Only email actions allowed",
                "No time or energy limits",
                "No task management required"
            ],
            "success_criteria": [
                "Classify emails correctly by urgency (≥70%)",
                "Handle VIP customers appropriately (≥80%)",
                "Choose appropriate actions for urgency levels (≥70%)",
                "Process all available emails"
            ],
            "evaluation_method": "Weighted combination of email handling accuracy and customer satisfaction",
            "learning_objectives": [
                "Understand email urgency classification",
                "Learn customer tier prioritization",
                "Master basic email action selection",
                "Develop customer service awareness"
            ]
        }