"""Medium task: Email Classification + Response Generation - OpsPilot Task Definition."""

from typing import Dict, Any, Optional, List
from env.environment import OpsPilotEnv
from models import Action, Observation, Reward


class TaskMedium:
    """
    Medium Task: Email Classification + Response Generation
    
    Objective: Classify emails AND generate appropriate responses with moderate constraints
    Focus: Email handling + response quality with basic resource awareness
    Difficulty: Intermediate level - dual objective optimization
    """
    
    def __init__(self):
        """Initialize medium task configuration."""
        self.task_name = "email_classification_and_response"
        self.difficulty = "medium"
        self.max_steps = 30
        self.objective = "Classify emails, generate appropriate responses, and manage basic constraints"
        
        # Task-specific configuration
        self.config = {
            "initial_emails": 6,
            "initial_tasks": 2,      # Few tasks for basic multitasking
            "initial_events": 1,     # One calendar constraint
            "time_limit": 400,       # Moderate time pressure (6.7 hours)
            "energy_limit": 80,      # Moderate energy constraint
            "focus_areas": ["email_classification", "response_generation", "basic_prioritization"]
        }
        
        # Evaluation criteria
        self.evaluation_weights = {
            "email_handling": 0.35,      # Primary focus
            "response_quality": 0.35,    # Primary focus
            "customer_satisfaction": 0.15, # Secondary
            "task_management": 0.10,     # Basic requirement
            "resource_efficiency": 0.05  # Light constraint
        }
    
    def create_environment(self, random_seed: int = 42) -> OpsPilotEnv:
        """
        Create environment configured for medium task.
        
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
        Validate that action is appropriate for medium task.
        
        Args:
            action: Action to validate
            observation: Current observation
            
        Returns:
            True if action is valid for this task
        """
        # Medium task requires email actions if emails are available
        if observation.emails and not action.email_actions:
            return False
        
        # Should handle tasks if they exist and are urgent
        urgent_tasks = [task for task in observation.tasks if task.deadline <= 60]
        if urgent_tasks and not action.task_priorities:
            return False
        
        # Validate individual actions
        for email_action in action.email_actions:
            if not self._validate_email_action(email_action, observation):
                return False
        
        for task_priority in action.task_priorities:
            if not self._validate_task_priority(task_priority, observation):
                return False
        
        # Check resource constraints
        if not self._check_resource_constraints(action, observation):
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
        
        # Medium task should include response content for replies
        if action_type == "reply" and "response_content" not in email_action:
            # Allow but note for evaluation
            pass
        
        return True
    
    def _validate_task_priority(self, task_priority: Dict[str, Any], observation: Observation) -> bool:
        """Validate task priority assignment."""
        task_id = task_priority.get("task_id")
        priority_level = task_priority.get("priority_level")
        
        # Check if task exists
        task_exists = any(task.task_id == task_id for task in observation.tasks)
        if not task_exists:
            return False
        
        # Check priority level range
        if not isinstance(priority_level, int) or not (1 <= priority_level <= 10):
            return False
        
        return True
    
    def _check_resource_constraints(self, action: Action, observation: Observation) -> bool:
        """Check if action respects resource constraints."""
        # Don't allow actions if energy is critically low
        if observation.energy_budget <= 10 and len(action.email_actions) > 2:
            return False
        
        # Don't allow too many simultaneous actions if time is limited
        if observation.time_remaining <= 60:
            total_actions = len(action.email_actions) + len(action.task_priorities)
            if total_actions > 3:
                return False
        
        return True
    
    def evaluate_performance(self, env: OpsPilotEnv) -> Dict[str, Any]:
        """
        Evaluate agent performance on medium task.
        
        Args:
            env: Environment after episode completion
            
        Returns:
            Evaluation results
        """
        state = env.state()
        
        # Calculate all evaluation metrics
        email_metrics = self._evaluate_email_handling(state)
        response_metrics = self._evaluate_response_quality(state)
        customer_metrics = self._evaluate_customer_satisfaction(state)
        task_metrics = self._evaluate_task_management(state)
        resource_metrics = self._evaluate_resource_efficiency(state)
        
        # Combine metrics with weights
        final_score = (
            email_metrics["score"] * self.evaluation_weights["email_handling"] +
            response_metrics["score"] * self.evaluation_weights["response_quality"] +
            customer_metrics["score"] * self.evaluation_weights["customer_satisfaction"] +
            task_metrics["score"] * self.evaluation_weights["task_management"] +
            resource_metrics["score"] * self.evaluation_weights["resource_efficiency"]
        )
        
        return {
            "task": self.task_name,
            "difficulty": self.difficulty,
            "final_score": final_score,
            "max_possible_score": 1.0,
            "performance_grade": self._get_performance_grade(final_score),
            "detailed_metrics": {
                "email_handling": email_metrics,
                "response_quality": response_metrics,
                "customer_satisfaction": customer_metrics,
                "task_management": task_metrics,
                "resource_efficiency": resource_metrics
            },
            "episode_stats": {
                "total_steps": state["current_step"],
                "total_reward": state["total_reward"],
                "emails_processed": self._count_emails_processed(state),
                "tasks_handled": self._count_tasks_handled(state),
                "completion_rate": self._calculate_completion_rate(state),
                "constraint_violations": self._count_constraint_violations(state)
            },
            "learning_feedback": self._generate_learning_feedback(
                email_metrics, response_metrics, customer_metrics, 
                task_metrics, resource_metrics
            )
        }
    
    def _evaluate_email_handling(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate email handling performance."""
        total_emails = len(state["ground_truth"]["email_labels"])
        if total_emails == 0:
            return {"score": 1.0, "details": "No emails to process"}
        
        correct_classifications = 0
        appropriate_actions = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for email_action in action.get("email_actions", []):
                email_id = email_action["email_id"]
                action_type = email_action["action_type"]
                
                if email_id in state["ground_truth"]["email_labels"]:
                    gt = state["ground_truth"]["email_labels"][email_id]
                    
                    if self._is_appropriate_action(action_type, gt):
                        appropriate_actions += 1
                    
                    if self._considers_customer_tier(action_type, gt):
                        correct_classifications += 1
        
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
    
    def _evaluate_response_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate response generation quality."""
        reply_actions = 0
        quality_responses = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for email_action in action.get("email_actions", []):
                if email_action["action_type"] == "reply":
                    reply_actions += 1
                    
                    # Check if response includes appropriate elements
                    response_content = email_action.get("response_content", "")
                    email_id = email_action["email_id"]
                    
                    if email_id in state["ground_truth"]["email_labels"]:
                        gt = state["ground_truth"]["email_labels"][email_id]
                        ideal_response = state["ground_truth"]["ideal_responses"].get(email_id, "")
                        
                        if self._is_quality_response(response_content, gt, ideal_response):
                            quality_responses += 1
        
        if reply_actions == 0:
            return {"score": 0.5, "details": "No reply actions taken"}
        
        quality_ratio = quality_responses / reply_actions
        
        return {
            "score": quality_ratio,
            "quality_responses": quality_responses,
            "total_replies": reply_actions,
            "quality_ratio": quality_ratio
        }
    
    def _evaluate_customer_satisfaction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate customer satisfaction metrics."""
        vip_handled = 0
        vip_total = 0
        urgent_handled = 0
        urgent_total = 0
        
        for email_id, gt in state["ground_truth"]["email_labels"].items():
            if gt["customer_tier"] == "vip":
                vip_total += 1
                if self._was_email_handled_appropriately(email_id, gt, state):
                    vip_handled += 1
            
            if gt["true_urgency"] >= 7:
                urgent_total += 1
                if self._was_email_handled_appropriately(email_id, gt, state):
                    urgent_handled += 1
        
        vip_satisfaction = vip_handled / vip_total if vip_total > 0 else 1.0
        urgency_satisfaction = urgent_handled / urgent_total if urgent_total > 0 else 1.0
        overall_satisfaction = (vip_satisfaction + urgency_satisfaction) / 2
        
        return {
            "score": overall_satisfaction,
            "vip_satisfaction": vip_satisfaction,
            "urgency_handling": urgency_satisfaction,
            "vip_handled": f"{vip_handled}/{vip_total}",
            "urgent_handled": f"{urgent_handled}/{urgent_total}"
        }
    
    def _evaluate_task_management(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate basic task management."""
        total_tasks = len(state["ground_truth"]["optimal_priorities"])
        if total_tasks == 0:
            return {"score": 1.0, "details": "No tasks to manage"}
        
        tasks_prioritized = 0
        correct_priorities = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for task_priority in action.get("task_priorities", []):
                task_id = task_priority["task_id"]
                assigned_priority = task_priority["priority_level"]
                
                if task_id in state["ground_truth"]["optimal_priorities"]:
                    tasks_prioritized += 1
                    optimal_priority = state["ground_truth"]["optimal_priorities"][task_id]
                    
                    # Allow ±2 difference for correct priority
                    if abs(assigned_priority - optimal_priority) <= 2:
                        correct_priorities += 1
        
        prioritization_score = correct_priorities / total_tasks if total_tasks > 0 else 0
        coverage_score = tasks_prioritized / total_tasks if total_tasks > 0 else 0
        overall_score = (prioritization_score + coverage_score) / 2
        
        return {
            "score": overall_score,
            "prioritization_accuracy": prioritization_score,
            "task_coverage": coverage_score,
            "tasks_prioritized": tasks_prioritized,
            "total_tasks": total_tasks
        }
    
    def _evaluate_resource_efficiency(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate resource usage efficiency."""
        final_time = state["time_remaining"]
        final_energy = state["energy_remaining"]
        
        # Calculate efficiency scores
        time_efficiency = 1.0 - (final_time / self.config["time_limit"])
        energy_efficiency = 1.0 - (final_energy / self.config["energy_limit"])
        
        # Penalize if resources were completely exhausted
        if final_time <= 0:
            time_efficiency *= 0.8  # Penalty for running out of time
        if final_energy <= 0:
            energy_efficiency *= 0.8  # Penalty for running out of energy
        
        overall_efficiency = (time_efficiency + energy_efficiency) / 2
        
        return {
            "score": max(0.0, overall_efficiency),
            "time_efficiency": max(0.0, time_efficiency),
            "energy_efficiency": max(0.0, energy_efficiency),
            "time_remaining": final_time,
            "energy_remaining": final_energy
        }
    
    def _is_appropriate_action(self, action_type: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if action type is appropriate for email urgency."""
        urgency = ground_truth["true_urgency"]
        
        if urgency >= 8:
            return action_type in ["reply", "escalate"]
        elif urgency >= 5:
            return action_type in ["reply", "defer"]
        else:
            return action_type in ["defer", "archive", "reply"]
    
    def _considers_customer_tier(self, action_type: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if action considers customer tier appropriately."""
        customer_tier = ground_truth["customer_tier"]
        
        if customer_tier == "vip":
            return action_type in ["reply", "escalate"]
        elif customer_tier == "premium":
            return action_type in ["reply", "defer"]
        else:
            return True
    
    def _is_quality_response(self, response_content: str, ground_truth: Dict[str, Any], 
                           ideal_response: str) -> bool:
        """Evaluate if response content is of good quality."""
        if not response_content:
            return False
        
        # Basic quality checks
        if len(response_content) < 20:  # Too short
            return False
        
        # Check for appropriate tone based on customer tier
        customer_tier = ground_truth["customer_tier"]
        if customer_tier == "vip" and "thank you" not in response_content.lower():
            return False
        
        # Check for urgency acknowledgment
        if ground_truth["true_urgency"] >= 8:
            urgency_words = ["urgent", "immediate", "priority", "asap"]
            if not any(word in response_content.lower() for word in urgency_words):
                return False
        
        return True
    
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
        
        return False
    
    def _count_emails_processed(self, state: Dict[str, Any]) -> int:
        """Count total emails processed."""
        count = 0
        for action_data in state["action_history"]:
            action = action_data["action"]
            count += len(action.get("email_actions", []))
        return count
    
    def _count_tasks_handled(self, state: Dict[str, Any]) -> int:
        """Count total tasks handled."""
        count = 0
        for action_data in state["action_history"]:
            action = action_data["action"]
            count += len(action.get("task_priorities", []))
        return count
    
    def _calculate_completion_rate(self, state: Dict[str, Any]) -> float:
        """Calculate overall completion rate."""
        total_items = (len(state["ground_truth"]["email_labels"]) + 
                      len(state["ground_truth"]["optimal_priorities"]))
        
        processed_items = self._count_emails_processed(state) + self._count_tasks_handled(state)
        
        return min(1.0, processed_items / total_items) if total_items > 0 else 1.0
    
    def _count_constraint_violations(self, state: Dict[str, Any]) -> int:
        """Count constraint violations."""
        violations = 0
        
        # Check if time ran out
        if state["time_remaining"] <= 0:
            violations += 1
        
        # Check if energy was depleted
        if state["energy_remaining"] <= 0:
            violations += 1
        
        return violations
    
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
                                  response_metrics: Dict[str, Any],
                                  customer_metrics: Dict[str, Any],
                                  task_metrics: Dict[str, Any],
                                  resource_metrics: Dict[str, Any]) -> List[str]:
        """Generate learning feedback for improvement."""
        feedback = []
        
        if email_metrics["score"] < 0.7:
            feedback.append("Improve email classification and action selection. "
                          "Focus on matching actions to urgency levels.")
        
        if response_metrics["score"] < 0.7:
            feedback.append("Enhance response quality. Include appropriate tone, "
                          "acknowledge urgency, and provide helpful content.")
        
        if customer_metrics["score"] < 0.8:
            feedback.append("Better prioritize VIP customers and urgent emails. "
                          "They need immediate attention.")
        
        if task_metrics["score"] < 0.6:
            feedback.append("Improve task prioritization. Consider both importance "
                          "and deadline when assigning priorities.")
        
        if resource_metrics["score"] < 0.5:
            feedback.append("Manage resources more efficiently. Avoid depleting "
                          "time or energy completely.")
        
        if not feedback:
            feedback.append("Great performance! You've mastered email classification "
                          "and response generation. Ready for hard difficulty tasks.")
        
        return feedback
    
    def get_task_description(self) -> Dict[str, Any]:
        """Get comprehensive task description."""
        return {
            "name": self.task_name,
            "difficulty": self.difficulty,
            "objective": self.objective,
            "max_steps": self.max_steps,
            "constraints": [
                "Moderate time limit (400 minutes)",
                "Moderate energy limit (80 points)",
                "Must handle both emails and basic tasks",
                "Response quality matters for replies"
            ],
            "success_criteria": [
                "Email classification accuracy ≥70%",
                "Response quality ≥70%",
                "VIP customer satisfaction ≥80%",
                "Task prioritization accuracy ≥60%",
                "Avoid resource depletion"
            ],
            "evaluation_method": "Weighted combination of email handling, response quality, customer satisfaction, task management, and resource efficiency",
            "learning_objectives": [
                "Master email classification and response generation",
                "Learn to balance multiple objectives",
                "Develop resource awareness",
                "Practice basic multitasking",
                "Understand constraint management"
            ]
        }