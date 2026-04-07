"""Hard task: Full System Management - OpsPilot Task Definition."""

from typing import Dict, Any, Optional, List
from env.environment import OpsPilotEnv
from models import Action, Observation, Reward


class TaskHard:
    """
    Hard Task: Full System Management
    
    Objective: Master complete operations management including email classification,
              response generation, task prioritization, scheduling, and resource optimization
    Focus: Multi-objective optimization under strict constraints
    Difficulty: Advanced level - complex system management
    """
    
    def __init__(self):
        """Initialize hard task configuration."""
        self.task_name = "full_system_management"
        self.difficulty = "hard"
        self.max_steps = 50
        self.objective = "Manage complete operations system with email handling, task prioritization, scheduling, and resource optimization"
        
        # Task-specific configuration
        self.config = {
            "initial_emails": 8,
            "initial_tasks": 5,      # Multiple competing tasks
            "initial_events": 3,     # Complex scheduling constraints
            "time_limit": 300,       # Strict time pressure (5 hours)
            "energy_limit": 60,      # Limited energy budget
            "focus_areas": [
                "email_classification", "response_generation", "task_prioritization",
                "scheduling_optimization", "resource_management", "conflict_resolution"
            ]
        }
        
        # Evaluation criteria
        self.evaluation_weights = {
            "email_handling": 0.20,        # Core competency
            "response_quality": 0.20,      # Core competency
            "task_management": 0.20,       # Core competency
            "scheduling_efficiency": 0.15, # Advanced skill
            "resource_efficiency": 0.15,   # Advanced skill
            "conflict_resolution": 0.10    # Expert skill
        }
    
    def create_environment(self, random_seed: int = 42) -> OpsPilotEnv:
        """
        Create environment configured for hard task.
        
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
        Validate that action is appropriate for hard task.
        
        Args:
            action: Action to validate
            observation: Current observation
            
        Returns:
            True if action is valid for this task
        """
        # Hard task requires comprehensive action planning
        if observation.emails and not action.email_actions:
            return False
        
        if observation.tasks and not action.task_priorities:
            return False
        
        # Must handle scheduling if there are conflicts
        if self._has_scheduling_conflicts(observation) and not action.scheduling:
            return False
        
        # Validate all action components
        if not self._validate_email_actions(action.email_actions, observation):
            return False
        
        if not self._validate_task_priorities(action.task_priorities, observation):
            return False
        
        if not self._validate_scheduling(action.scheduling, observation):
            return False
        
        # Check resource constraints
        if not self._check_resource_constraints(action, observation):
            return False
        
        # Check for conflicts and inefficiencies
        if not self._check_action_consistency(action, observation):
            return False
        
        return True
    
    def _validate_email_actions(self, email_actions: List[Dict[str, Any]], 
                               observation: Observation) -> bool:
        """Validate email actions comprehensively."""
        for email_action in email_actions:
            email_id = email_action.get("email_id")
            action_type = email_action.get("action_type")
            
            # Check email exists
            email_exists = any(email.id == email_id for email in observation.emails)
            if not email_exists:
                return False
            
            # Check action type validity
            valid_actions = ["reply", "escalate", "defer", "archive"]
            if action_type not in valid_actions:
                return False
            
            # Hard task requires response content for replies
            if action_type == "reply" and not email_action.get("response_content"):
                return False
            
            # Check escalation reasoning
            if action_type == "escalate" and not email_action.get("escalation_reason"):
                return False
        
        return True
    
    def _validate_task_priorities(self, task_priorities: List[Dict[str, Any]], 
                                 observation: Observation) -> bool:
        """Validate task priority assignments."""
        for task_priority in task_priorities:
            task_id = task_priority.get("task_id")
            priority_level = task_priority.get("priority_level")
            
            # Check task exists
            task_exists = any(task.task_id == task_id for task in observation.tasks)
            if not task_exists:
                return False
            
            # Check priority level
            if not isinstance(priority_level, int) or not (1 <= priority_level <= 10):
                return False
            
            # Hard task should include reasoning
            if not task_priority.get("reasoning"):
                return False
        
        return True
    
    def _validate_scheduling(self, scheduling: List[Dict[str, Any]], 
                           observation: Observation) -> bool:
        """Validate scheduling decisions."""
        for schedule_item in scheduling:
            item_id = schedule_item.get("item_id")
            item_type = schedule_item.get("item_type")
            scheduled_time = schedule_item.get("scheduled_time")
            duration = schedule_item.get("duration")
            
            # Check item type
            if item_type not in ["task", "email", "meeting"]:
                return False
            
            # Check time validity
            if not isinstance(scheduled_time, int) or scheduled_time < 0:
                return False
            
            # Check duration
            if not isinstance(duration, int) or duration <= 0:
                return False
            
            # Check if item exists
            if item_type == "task":
                item_exists = any(task.task_id == item_id for task in observation.tasks)
            elif item_type == "email":
                item_exists = any(email.id == item_id for email in observation.emails)
            else:  # meeting
                item_exists = any(event.event_id == item_id for event in observation.calendar)
            
            if not item_exists:
                return False
        
        return True
    
    def _has_scheduling_conflicts(self, observation: Observation) -> bool:
        """Check if there are potential scheduling conflicts."""
        # Check for overlapping calendar events
        events = sorted(observation.calendar, key=lambda x: x.time)
        for i in range(len(events) - 1):
            current_end = events[i].time + events[i].duration
            next_start = events[i + 1].time
            if current_end > next_start:
                return True
        
        # Check for urgent tasks with tight deadlines
        urgent_tasks = [task for task in observation.tasks if task.deadline <= 120]
        if len(urgent_tasks) > 2:
            return True
        
        return False
    
    def _check_resource_constraints(self, action: Action, observation: Observation) -> bool:
        """Check comprehensive resource constraints."""
        # Energy constraints
        estimated_energy_cost = self._estimate_energy_cost(action)
        if observation.energy_budget < estimated_energy_cost:
            return False
        
        # Time constraints
        estimated_time_cost = self._estimate_time_cost(action)
        if observation.time_remaining < estimated_time_cost:
            return False
        
        # Don't overcommit resources
        if (estimated_energy_cost > observation.energy_budget * 0.8 and 
            estimated_time_cost > observation.time_remaining * 0.8):
            return False
        
        return True
    
    def _check_action_consistency(self, action: Action, observation: Observation) -> bool:
        """Check for internal action consistency."""
        # Check for conflicting priorities
        priorities = [tp["priority_level"] for tp in action.task_priorities]
        if len(priorities) != len(set(priorities)) and len(priorities) > 1:
            # Duplicate priorities are allowed but should be reasonable
            pass
        
        # Check scheduling conflicts
        scheduled_times = {}
        for schedule_item in action.scheduling:
            start_time = schedule_item["scheduled_time"]
            end_time = start_time + schedule_item["duration"]
            
            for existing_start, existing_end in scheduled_times.values():
                if not (end_time <= existing_start or start_time >= existing_end):
                    return False  # Overlap detected
            
            scheduled_times[schedule_item["item_id"]] = (start_time, end_time)
        
        return True
    
    def _estimate_energy_cost(self, action: Action) -> int:
        """Estimate energy cost of action."""
        cost = 0
        cost += len(action.email_actions) * 5  # 5 energy per email action
        cost += len(action.task_priorities) * 3  # 3 energy per task prioritization
        cost += len(action.scheduling) * 4  # 4 energy per scheduling decision
        return cost
    
    def _estimate_time_cost(self, action: Action) -> int:
        """Estimate time cost of action."""
        cost = 0
        cost += len(action.email_actions) * 10  # 10 minutes per email
        cost += len(action.task_priorities) * 5   # 5 minutes per task priority
        cost += len(action.scheduling) * 8       # 8 minutes per scheduling decision
        return cost
    
    def evaluate_performance(self, env: OpsPilotEnv) -> Dict[str, Any]:
        """
        Evaluate agent performance on hard task.
        
        Args:
            env: Environment after episode completion
            
        Returns:
            Comprehensive evaluation results
        """
        state = env.state()
        
        # Calculate all evaluation metrics
        email_metrics = self._evaluate_email_handling(state)
        response_metrics = self._evaluate_response_quality(state)
        task_metrics = self._evaluate_task_management(state)
        scheduling_metrics = self._evaluate_scheduling_efficiency(state)
        resource_metrics = self._evaluate_resource_efficiency(state)
        conflict_metrics = self._evaluate_conflict_resolution(state)
        
        # Combine metrics with weights
        final_score = (
            email_metrics["score"] * self.evaluation_weights["email_handling"] +
            response_metrics["score"] * self.evaluation_weights["response_quality"] +
            task_metrics["score"] * self.evaluation_weights["task_management"] +
            scheduling_metrics["score"] * self.evaluation_weights["scheduling_efficiency"] +
            resource_metrics["score"] * self.evaluation_weights["resource_efficiency"] +
            conflict_metrics["score"] * self.evaluation_weights["conflict_resolution"]
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
                "task_management": task_metrics,
                "scheduling_efficiency": scheduling_metrics,
                "resource_efficiency": resource_metrics,
                "conflict_resolution": conflict_metrics
            },
            "episode_stats": {
                "total_steps": state["current_step"],
                "total_reward": state["total_reward"],
                "emails_processed": self._count_emails_processed(state),
                "tasks_handled": self._count_tasks_handled(state),
                "scheduling_decisions": self._count_scheduling_decisions(state),
                "completion_rate": self._calculate_completion_rate(state),
                "constraint_violations": self._count_constraint_violations(state),
                "conflicts_resolved": self._count_conflicts_resolved(state)
            },
            "learning_feedback": self._generate_learning_feedback(
                email_metrics, response_metrics, task_metrics,
                scheduling_metrics, resource_metrics, conflict_metrics
            ),
            "expert_analysis": self._generate_expert_analysis(state)
        }
    
    def _evaluate_email_handling(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate comprehensive email handling performance."""
        total_emails = len(state["ground_truth"]["email_labels"])
        if total_emails == 0:
            return {"score": 1.0, "details": "No emails to process"}
        
        correct_classifications = 0
        appropriate_actions = 0
        vip_handled_correctly = 0
        vip_total = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for email_action in action.get("email_actions", []):
                email_id = email_action["email_id"]
                action_type = email_action["action_type"]
                
                if email_id in state["ground_truth"]["email_labels"]:
                    gt = state["ground_truth"]["email_labels"][email_id]
                    
                    # Check action appropriateness
                    if self._is_appropriate_action(action_type, gt):
                        appropriate_actions += 1
                    
                    # Check classification accuracy
                    if self._considers_customer_tier(action_type, gt):
                        correct_classifications += 1
                    
                    # Track VIP handling
                    if gt["customer_tier"] == "vip":
                        vip_total += 1
                        if action_type in ["reply", "escalate"]:
                            vip_handled_correctly += 1
        
        # Calculate scores
        classification_score = correct_classifications / total_emails if total_emails > 0 else 0
        action_score = appropriate_actions / total_emails if total_emails > 0 else 0
        vip_score = vip_handled_correctly / vip_total if vip_total > 0 else 1.0
        
        overall_score = (classification_score * 0.4 + action_score * 0.4 + vip_score * 0.2)
        
        return {
            "score": overall_score,
            "classification_accuracy": classification_score,
            "action_appropriateness": action_score,
            "vip_handling": vip_score,
            "emails_handled": appropriate_actions,
            "total_emails": total_emails,
            "vip_emails_handled": f"{vip_handled_correctly}/{vip_total}"
        }
    
    def _evaluate_response_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate response generation quality with advanced criteria."""
        reply_actions = 0
        high_quality_responses = 0
        appropriate_tone = 0
        complete_responses = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for email_action in action.get("email_actions", []):
                if email_action["action_type"] == "reply":
                    reply_actions += 1
                    response_content = email_action.get("response_content", "")
                    email_id = email_action["email_id"]
                    
                    if email_id in state["ground_truth"]["email_labels"]:
                        gt = state["ground_truth"]["email_labels"][email_id]
                        ideal_response = state["ground_truth"]["ideal_responses"].get(email_id, "")
                        
                        # Check response completeness
                        if self._is_complete_response(response_content, gt):
                            complete_responses += 1
                        
                        # Check tone appropriateness
                        if self._has_appropriate_tone(response_content, gt):
                            appropriate_tone += 1
                        
                        # Overall quality assessment
                        if self._is_high_quality_response(response_content, gt, ideal_response):
                            high_quality_responses += 1
        
        if reply_actions == 0:
            return {"score": 0.3, "details": "No reply actions taken"}
        
        quality_ratio = high_quality_responses / reply_actions
        tone_ratio = appropriate_tone / reply_actions
        completeness_ratio = complete_responses / reply_actions
        
        overall_score = (quality_ratio * 0.5 + tone_ratio * 0.3 + completeness_ratio * 0.2)
        
        return {
            "score": overall_score,
            "quality_ratio": quality_ratio,
            "tone_appropriateness": tone_ratio,
            "completeness_ratio": completeness_ratio,
            "high_quality_responses": high_quality_responses,
            "total_replies": reply_actions
        }
    
    def _evaluate_task_management(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate advanced task management and prioritization."""
        total_tasks = len(state["ground_truth"]["optimal_priorities"])
        if total_tasks == 0:
            return {"score": 1.0, "details": "No tasks to manage"}
        
        tasks_prioritized = 0
        correct_priorities = 0
        deadline_awareness = 0
        importance_consideration = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for task_priority in action.get("task_priorities", []):
                task_id = task_priority["task_id"]
                assigned_priority = task_priority["priority_level"]
                reasoning = task_priority.get("reasoning", "")
                
                if task_id in state["ground_truth"]["optimal_priorities"]:
                    tasks_prioritized += 1
                    optimal_priority = state["ground_truth"]["optimal_priorities"][task_id]
                    
                    # Check priority accuracy (±1 for hard task)
                    if abs(assigned_priority - optimal_priority) <= 1:
                        correct_priorities += 1
                    
                    # Check if reasoning mentions deadline
                    if "deadline" in reasoning.lower() or "due" in reasoning.lower():
                        deadline_awareness += 1
                    
                    # Check if reasoning mentions importance
                    if "important" in reasoning.lower() or "critical" in reasoning.lower():
                        importance_consideration += 1
        
        # Calculate scores
        prioritization_score = correct_priorities / total_tasks if total_tasks > 0 else 0
        coverage_score = tasks_prioritized / total_tasks if total_tasks > 0 else 0
        reasoning_score = ((deadline_awareness + importance_consideration) / 
                          (2 * tasks_prioritized)) if tasks_prioritized > 0 else 0
        
        overall_score = (prioritization_score * 0.5 + coverage_score * 0.3 + reasoning_score * 0.2)
        
        return {
            "score": overall_score,
            "prioritization_accuracy": prioritization_score,
            "task_coverage": coverage_score,
            "reasoning_quality": reasoning_score,
            "tasks_prioritized": tasks_prioritized,
            "total_tasks": total_tasks,
            "deadline_awareness": deadline_awareness,
            "importance_consideration": importance_consideration
        }
    
    def _evaluate_scheduling_efficiency(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate scheduling optimization and conflict resolution."""
        total_scheduling_decisions = 0
        optimal_scheduling = 0
        conflict_free_schedules = 0
        resource_efficient_schedules = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            for schedule_item in action.get("scheduling", []):
                total_scheduling_decisions += 1
                item_id = schedule_item["item_id"]
                scheduled_time = schedule_item["scheduled_time"]
                duration = schedule_item["duration"]
                
                # Check if scheduling is optimal
                if self._is_optimal_scheduling(schedule_item, state):
                    optimal_scheduling += 1
                
                # Check for conflicts
                if self._is_conflict_free_schedule(schedule_item, action.scheduling):
                    conflict_free_schedules += 1
                
                # Check resource efficiency
                if self._is_resource_efficient_schedule(schedule_item, state):
                    resource_efficient_schedules += 1
        
        if total_scheduling_decisions == 0:
            return {"score": 0.5, "details": "No scheduling decisions made"}
        
        # Calculate scores
        optimization_score = optimal_scheduling / total_scheduling_decisions
        conflict_resolution_score = conflict_free_schedules / total_scheduling_decisions
        efficiency_score = resource_efficient_schedules / total_scheduling_decisions
        
        overall_score = (optimization_score * 0.4 + conflict_resolution_score * 0.4 + 
                        efficiency_score * 0.2)
        
        return {
            "score": overall_score,
            "optimization_score": optimization_score,
            "conflict_resolution_score": conflict_resolution_score,
            "efficiency_score": efficiency_score,
            "total_scheduling_decisions": total_scheduling_decisions,
            "optimal_schedules": optimal_scheduling,
            "conflict_free_schedules": conflict_free_schedules
        }
    
    def _evaluate_resource_efficiency(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate resource management and optimization."""
        initial_time = self.config["time_limit"]
        initial_energy = self.config["energy_limit"]
        
        final_time = state["time_remaining"]
        final_energy = state["energy_remaining"]
        
        # Calculate utilization rates
        time_utilization = (initial_time - final_time) / initial_time
        energy_utilization = (initial_energy - final_energy) / initial_energy
        
        # Calculate efficiency scores
        time_efficiency = self._calculate_time_efficiency(state)
        energy_efficiency = self._calculate_energy_efficiency(state)
        
        # Penalize resource exhaustion
        exhaustion_penalty = 0
        if final_time <= 0:
            exhaustion_penalty += 0.3
        if final_energy <= 0:
            exhaustion_penalty += 0.3
        
        # Reward optimal resource usage (80-95% utilization is ideal)
        optimal_utilization_bonus = 0
        if 0.8 <= time_utilization <= 0.95:
            optimal_utilization_bonus += 0.1
        if 0.8 <= energy_utilization <= 0.95:
            optimal_utilization_bonus += 0.1
        
        overall_score = max(0.0, (time_efficiency + energy_efficiency) / 2 - 
                           exhaustion_penalty + optimal_utilization_bonus)
        
        return {
            "score": min(1.0, overall_score),
            "time_efficiency": time_efficiency,
            "energy_efficiency": energy_efficiency,
            "time_utilization": time_utilization,
            "energy_utilization": energy_utilization,
            "time_remaining": final_time,
            "energy_remaining": final_energy,
            "exhaustion_penalty": exhaustion_penalty,
            "optimal_utilization_bonus": optimal_utilization_bonus
        }
    
    def _evaluate_conflict_resolution(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate conflict identification and resolution capabilities."""
        total_conflicts = self._count_total_conflicts(state)
        resolved_conflicts = self._count_resolved_conflicts(state)
        prevention_actions = self._count_prevention_actions(state)
        
        if total_conflicts == 0:
            # No conflicts is good, but check if prevention was used
            prevention_score = min(1.0, prevention_actions / 3)  # Up to 3 prevention actions
            return {
                "score": 0.8 + (prevention_score * 0.2),
                "details": "No conflicts detected",
                "prevention_score": prevention_score,
                "prevention_actions": prevention_actions
            }
        
        # Calculate resolution effectiveness
        resolution_rate = resolved_conflicts / total_conflicts
        
        # Bonus for proactive conflict prevention
        prevention_bonus = min(0.2, prevention_actions * 0.05)
        
        overall_score = min(1.0, resolution_rate + prevention_bonus)
        
        return {
            "score": overall_score,
            "resolution_rate": resolution_rate,
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "prevention_actions": prevention_actions,
            "prevention_bonus": prevention_bonus
        }
    
    # Helper methods for evaluation
    def _is_appropriate_action(self, action_type: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if action type is appropriate for email urgency and context."""
        urgency = ground_truth["true_urgency"]
        customer_tier = ground_truth["customer_tier"]
        
        if urgency >= 9 or customer_tier == "vip":
            return action_type in ["reply", "escalate"]
        elif urgency >= 7:
            return action_type in ["reply", "escalate", "defer"]
        elif urgency >= 4:
            return action_type in ["reply", "defer"]
        else:
            return action_type in ["defer", "archive"]
    
    def _considers_customer_tier(self, action_type: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if action appropriately considers customer tier."""
        customer_tier = ground_truth["customer_tier"]
        
        if customer_tier == "vip":
            return action_type in ["reply", "escalate"]
        elif customer_tier == "premium":
            return action_type in ["reply", "defer", "escalate"]
        else:  # free
            return True  # Any reasonable action is acceptable
    
    def _is_complete_response(self, response_content: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if response is complete and addresses the email properly."""
        if len(response_content) < 50:  # Minimum length for completeness
            return False
        
        # Check for key elements
        has_greeting = any(word in response_content.lower() 
                          for word in ["hello", "hi", "dear", "greetings"])
        has_closing = any(word in response_content.lower() 
                         for word in ["regards", "sincerely", "thanks", "best"])
        has_substance = len(response_content.split()) >= 20
        
        return has_greeting and has_closing and has_substance
    
    def _has_appropriate_tone(self, response_content: str, ground_truth: Dict[str, Any]) -> bool:
        """Check if response tone matches customer tier and urgency."""
        customer_tier = ground_truth["customer_tier"]
        urgency = ground_truth["true_urgency"]
        
        content_lower = response_content.lower()
        
        # VIP customers should get premium tone
        if customer_tier == "vip":
            vip_indicators = ["appreciate", "valued", "priority", "immediately", "personally"]
            if not any(indicator in content_lower for indicator in vip_indicators):
                return False
        
        # High urgency should be acknowledged
        if urgency >= 8:
            urgency_indicators = ["urgent", "immediate", "priority", "asap", "quickly"]
            if not any(indicator in content_lower for indicator in urgency_indicators):
                return False
        
        return True
    
    def _is_high_quality_response(self, response_content: str, ground_truth: Dict[str, Any], 
                                 ideal_response: str) -> bool:
        """Comprehensive response quality assessment."""
        if not response_content:
            return False
        
        # Basic quality checks
        if not self._is_complete_response(response_content, ground_truth):
            return False
        
        if not self._has_appropriate_tone(response_content, ground_truth):
            return False
        
        # Check for personalization
        if ground_truth["customer_tier"] == "vip":
            personalization_indicators = ["personally", "specifically", "individual", "custom"]
            if not any(indicator in response_content.lower() for indicator in personalization_indicators):
                return False
        
        # Check for solution-oriented content
        solution_indicators = ["solution", "resolve", "fix", "help", "assist", "address"]
        if not any(indicator in response_content.lower() for indicator in solution_indicators):
            return False
        
        return True
    
    def _is_optimal_scheduling(self, schedule_item: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Check if scheduling decision is optimal."""
        item_id = schedule_item["item_id"]
        scheduled_time = schedule_item["scheduled_time"]
        
        # Check against optimal schedules in ground truth
        optimal_schedules = state["ground_truth"].get("optimal_schedules", {})
        if item_id in optimal_schedules:
            optimal_time = optimal_schedules[item_id]["time"]
            # Allow ±30 minutes flexibility
            return abs(scheduled_time - optimal_time) <= 30
        
        return True  # If no ground truth, assume reasonable
    
    def _is_conflict_free_schedule(self, schedule_item: Dict[str, Any], 
                                  all_scheduling: List[Dict[str, Any]]) -> bool:
        """Check if schedule item conflicts with others."""
        item_start = schedule_item["scheduled_time"]
        item_end = item_start + schedule_item["duration"]
        
        for other_item in all_scheduling:
            if other_item["item_id"] == schedule_item["item_id"]:
                continue
            
            other_start = other_item["scheduled_time"]
            other_end = other_start + other_item["duration"]
            
            # Check for overlap
            if not (item_end <= other_start or item_start >= other_end):
                return False
        
        return True
    
    def _is_resource_efficient_schedule(self, schedule_item: Dict[str, Any], 
                                       state: Dict[str, Any]) -> bool:
        """Check if schedule is resource-efficient."""
        duration = schedule_item["duration"]
        item_type = schedule_item["item_type"]
        
        # Check if duration is reasonable for item type
        if item_type == "email" and duration > 30:
            return False  # Emails shouldn't take more than 30 minutes
        elif item_type == "task" and duration < 15:
            return False  # Tasks need at least 15 minutes
        elif item_type == "meeting" and duration < 30:
            return False  # Meetings need at least 30 minutes
        
        return True
    
    def _calculate_time_efficiency(self, state: Dict[str, Any]) -> float:
        """Calculate time usage efficiency."""
        total_actions = sum(len(action_data["action"].get("email_actions", [])) +
                           len(action_data["action"].get("task_priorities", [])) +
                           len(action_data["action"].get("scheduling", []))
                           for action_data in state["action_history"])
        
        if total_actions == 0:
            return 0.0
        
        time_used = self.config["time_limit"] - state["time_remaining"]
        time_per_action = time_used / total_actions if total_actions > 0 else 0
        
        # Optimal time per action is around 15-20 minutes
        if 15 <= time_per_action <= 20:
            return 1.0
        elif 10 <= time_per_action <= 25:
            return 0.8
        elif 5 <= time_per_action <= 30:
            return 0.6
        else:
            return 0.4
    
    def _calculate_energy_efficiency(self, state: Dict[str, Any]) -> float:
        """Calculate energy usage efficiency."""
        total_actions = sum(len(action_data["action"].get("email_actions", [])) +
                           len(action_data["action"].get("task_priorities", [])) +
                           len(action_data["action"].get("scheduling", []))
                           for action_data in state["action_history"])
        
        if total_actions == 0:
            return 0.0
        
        energy_used = self.config["energy_limit"] - state["energy_remaining"]
        energy_per_action = energy_used / total_actions if total_actions > 0 else 0
        
        # Optimal energy per action is around 3-5 points
        if 3 <= energy_per_action <= 5:
            return 1.0
        elif 2 <= energy_per_action <= 6:
            return 0.8
        elif 1 <= energy_per_action <= 8:
            return 0.6
        else:
            return 0.4
    
    def _count_total_conflicts(self, state: Dict[str, Any]) -> int:
        """Count total conflicts that occurred during episode."""
        conflicts = 0
        
        # Check for scheduling conflicts in action history
        for action_data in state["action_history"]:
            scheduling = action_data["action"].get("scheduling", [])
            for i, item1 in enumerate(scheduling):
                for item2 in scheduling[i+1:]:
                    if self._items_conflict(item1, item2):
                        conflicts += 1
        
        # Check for resource conflicts
        for action_data in state["action_history"]:
            observation = action_data["observation"]
            if observation["energy_budget"] <= 10 and observation["time_remaining"] <= 60:
                conflicts += 1  # Resource conflict
        
        return conflicts
    
    def _count_resolved_conflicts(self, state: Dict[str, Any]) -> int:
        """Count conflicts that were successfully resolved."""
        resolved = 0
        
        # Check if scheduling conflicts were resolved in subsequent actions
        for i, action_data in enumerate(state["action_history"]):
            scheduling = action_data["action"].get("scheduling", [])
            conflicts_in_action = 0
            
            for j, item1 in enumerate(scheduling):
                for item2 in scheduling[j+1:]:
                    if self._items_conflict(item1, item2):
                        conflicts_in_action += 1
            
            # Check if conflicts were resolved in next action
            if i < len(state["action_history"]) - 1:
                next_scheduling = state["action_history"][i+1]["action"].get("scheduling", [])
                conflicts_in_next = 0
                
                for j, item1 in enumerate(next_scheduling):
                    for item2 in next_scheduling[j+1:]:
                        if self._items_conflict(item1, item2):
                            conflicts_in_next += 1
                
                if conflicts_in_action > conflicts_in_next:
                    resolved += (conflicts_in_action - conflicts_in_next)
        
        return resolved
    
    def _count_prevention_actions(self, state: Dict[str, Any]) -> int:
        """Count proactive conflict prevention actions."""
        prevention_actions = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            
            # Check for buffer time in scheduling
            for schedule_item in action.get("scheduling", []):
                if schedule_item.get("buffer_time", 0) > 0:
                    prevention_actions += 1
            
            # Check for early task prioritization
            for task_priority in action.get("task_priorities", []):
                if "early" in task_priority.get("reasoning", "").lower():
                    prevention_actions += 1
            
            # Check for proactive email handling
            for email_action in action.get("email_actions", []):
                if email_action["action_type"] == "escalate":
                    prevention_actions += 1
        
        return prevention_actions
    
    def _items_conflict(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if two scheduled items conflict."""
        start1 = item1["scheduled_time"]
        end1 = start1 + item1["duration"]
        start2 = item2["scheduled_time"]
        end2 = start2 + item2["duration"]
        
        return not (end1 <= start2 or start1 >= end2)
    
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
    
    def _count_scheduling_decisions(self, state: Dict[str, Any]) -> int:
        """Count total scheduling decisions made."""
        count = 0
        for action_data in state["action_history"]:
            action = action_data["action"]
            count += len(action.get("scheduling", []))
        return count
    
    def _calculate_completion_rate(self, state: Dict[str, Any]) -> float:
        """Calculate overall task completion rate."""
        total_items = (len(state["ground_truth"]["email_labels"]) + 
                      len(state["ground_truth"]["optimal_priorities"]))
        
        processed_items = (self._count_emails_processed(state) + 
                          self._count_tasks_handled(state))
        
        return min(1.0, processed_items / total_items) if total_items > 0 else 1.0
    
    def _count_constraint_violations(self, state: Dict[str, Any]) -> int:
        """Count various constraint violations."""
        violations = 0
        
        # Resource exhaustion
        if state["time_remaining"] <= 0:
            violations += 1
        if state["energy_remaining"] <= 0:
            violations += 1
        
        # Scheduling conflicts
        for action_data in state["action_history"]:
            scheduling = action_data["action"].get("scheduling", [])
            for i, item1 in enumerate(scheduling):
                for item2 in scheduling[i+1:]:
                    if self._items_conflict(item1, item2):
                        violations += 1
        
        return violations
    
    def _count_conflicts_resolved(self, state: Dict[str, Any]) -> int:
        """Count total conflicts resolved during episode."""
        return self._count_resolved_conflicts(state)
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert score to performance grade with expert-level standards."""
        if score >= 0.95:
            return "A+ (Expert)"
        elif score >= 0.90:
            return "A (Excellent)"
        elif score >= 0.80:
            return "B+ (Very Good)"
        elif score >= 0.70:
            return "B (Good)"
        elif score >= 0.60:
            return "C+ (Satisfactory)"
        elif score >= 0.50:
            return "C (Needs Improvement)"
        else:
            return "F (Poor - Requires Significant Work)"
    
    def _generate_learning_feedback(self, email_metrics: Dict[str, Any], 
                                  response_metrics: Dict[str, Any],
                                  task_metrics: Dict[str, Any],
                                  scheduling_metrics: Dict[str, Any],
                                  resource_metrics: Dict[str, Any],
                                  conflict_metrics: Dict[str, Any]) -> List[str]:
        """Generate comprehensive learning feedback for improvement."""
        feedback = []
        
        # Email handling feedback
        if email_metrics["score"] < 0.8:
            feedback.append("Improve email classification accuracy and action selection. "
                          "Focus on urgency assessment and customer tier prioritization.")
        
        # Response quality feedback
        if response_metrics["score"] < 0.8:
            feedback.append("Enhance response quality by including proper greetings, closings, "
                          "and solution-oriented content. Adjust tone for VIP customers.")
        
        # Task management feedback
        if task_metrics["score"] < 0.7:
            feedback.append("Strengthen task prioritization by considering both deadlines and "
                          "importance. Provide clear reasoning for priority assignments.")
        
        # Scheduling feedback
        if scheduling_metrics["score"] < 0.7:
            feedback.append("Optimize scheduling decisions to avoid conflicts and maximize "
                          "resource efficiency. Consider buffer times between activities.")
        
        # Resource management feedback
        if resource_metrics["score"] < 0.6:
            feedback.append("Improve resource management by balancing time and energy usage. "
                          "Avoid complete resource exhaustion while maintaining productivity.")
        
        # Conflict resolution feedback
        if conflict_metrics["score"] < 0.7:
            feedback.append("Develop better conflict identification and resolution skills. "
                          "Practice proactive conflict prevention strategies.")
        
        # Advanced feedback for high performers
        if all(metric["score"] >= 0.8 for metric in [email_metrics, response_metrics, 
                                                     task_metrics, scheduling_metrics]):
            if resource_metrics["score"] < 0.9:
                feedback.append("Focus on optimizing resource utilization for expert-level "
                              "performance. Aim for 85-90% resource utilization.")
            
            if conflict_metrics["score"] < 0.9:
                feedback.append("Master advanced conflict resolution by implementing more "
                              "proactive prevention strategies and faster resolution times.")
        
        # Expert-level achievement
        if not feedback:
            feedback.append("Outstanding performance! You've achieved expert-level operations "
                          "management. Consider mentoring others or tackling specialized scenarios.")
        
        return feedback
    
    def _generate_expert_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate expert-level performance analysis."""
        analysis = {
            "strengths": [],
            "improvement_areas": [],
            "strategic_insights": [],
            "next_level_recommendations": []
        }
        
        # Analyze decision patterns
        decision_patterns = self._analyze_decision_patterns(state)
        
        # Identify strengths
        if decision_patterns["consistent_prioritization"]:
            analysis["strengths"].append("Consistent task prioritization methodology")
        
        if decision_patterns["proactive_scheduling"]:
            analysis["strengths"].append("Proactive scheduling and conflict prevention")
        
        if decision_patterns["customer_awareness"]:
            analysis["strengths"].append("Strong customer tier awareness and appropriate handling")
        
        # Identify improvement areas
        if decision_patterns["resource_waste"] > 0.2:
            analysis["improvement_areas"].append("Resource utilization optimization")
        
        if decision_patterns["reactive_responses"] > 0.3:
            analysis["improvement_areas"].append("Shift from reactive to proactive management")
        
        # Strategic insights
        total_actions = len([action for action_data in state["action_history"] 
                           for action in action_data["action"].get("email_actions", [])])
        
        if total_actions > 0:
            avg_response_time = (self.config["time_limit"] - state["time_remaining"]) / total_actions
            analysis["strategic_insights"].append(
                f"Average action processing time: {avg_response_time:.1f} minutes"
            )
        
        # Next level recommendations
        completion_rate = self._calculate_completion_rate(state)
        if completion_rate >= 0.9:
            analysis["next_level_recommendations"].append(
                "Ready for real-world operations management scenarios"
            )
        else:
            analysis["next_level_recommendations"].append(
                "Focus on improving completion rate before advancing"
            )
        
        return analysis
    
    def _analyze_decision_patterns(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze decision-making patterns throughout the episode."""
        patterns = {
            "consistent_prioritization": False,
            "proactive_scheduling": False,
            "customer_awareness": False,
            "resource_waste": 0.0,
            "reactive_responses": 0.0
        }
        
        # Analyze prioritization consistency
        priority_assignments = []
        for action_data in state["action_history"]:
            for task_priority in action_data["action"].get("task_priorities", []):
                priority_assignments.append(task_priority["priority_level"])
        
        if len(priority_assignments) > 1:
            priority_variance = sum((p - sum(priority_assignments)/len(priority_assignments))**2 
                                  for p in priority_assignments) / len(priority_assignments)
            patterns["consistent_prioritization"] = priority_variance < 4.0  # Low variance
        
        # Analyze proactive vs reactive behavior
        proactive_actions = 0
        total_actions = 0
        
        for action_data in state["action_history"]:
            action = action_data["action"]
            total_actions += 1
            
            # Check for proactive indicators
            if (len(action.get("scheduling", [])) > 0 or 
                any("prevent" in tp.get("reasoning", "").lower() 
                    for tp in action.get("task_priorities", []))):
                proactive_actions += 1
        
        if total_actions > 0:
            patterns["reactive_responses"] = 1.0 - (proactive_actions / total_actions)
        
        # Analyze customer awareness
        vip_appropriate_actions = 0
        vip_total_actions = 0
        
        for action_data in state["action_history"]:
            for email_action in action_data["action"].get("email_actions", []):
                email_id = email_action["email_id"]
                if email_id in state["ground_truth"]["email_labels"]:
                    gt = state["ground_truth"]["email_labels"][email_id]
                    if gt["customer_tier"] == "vip":
                        vip_total_actions += 1
                        if email_action["action_type"] in ["reply", "escalate"]:
                            vip_appropriate_actions += 1
        
        if vip_total_actions > 0:
            patterns["customer_awareness"] = (vip_appropriate_actions / vip_total_actions) >= 0.8
        
        # Calculate resource waste
        time_waste = max(0, state["time_remaining"] / self.config["time_limit"])
        energy_waste = max(0, state["energy_remaining"] / self.config["energy_limit"])
        patterns["resource_waste"] = (time_waste + energy_waste) / 2
        
        return patterns
    
    def get_task_description(self) -> Dict[str, Any]:
        """Get comprehensive task description."""
        return {
            "name": self.task_name,
            "difficulty": self.difficulty,
            "objective": self.objective,
            "max_steps": self.max_steps,
            "constraints": [
                "Strict time limit (300 minutes)",
                "Limited energy budget (60 points)",
                "Multiple competing priorities",
                "Complex scheduling requirements",
                "Resource optimization required",
                "Conflict resolution mandatory"
            ],
            "success_criteria": [
                "Email handling accuracy ≥80%",
                "Response quality ≥80%",
                "Task prioritization accuracy ≥70%",
                "Scheduling efficiency ≥70%",
                "Resource efficiency ≥60%",
                "Conflict resolution ≥70%",
                "Overall completion rate ≥90%"
            ],
            "evaluation_method": "Comprehensive weighted evaluation across six core competencies with expert-level standards",
            "learning_objectives": [
                "Master multi-objective optimization under constraints",
                "Develop expert-level resource management skills",
                "Learn advanced conflict identification and resolution",
                "Practice complex scheduling optimization",
                "Integrate all operations management competencies",
                "Achieve expert-level decision-making consistency"
            ],
            "expert_skills_required": [
                "Strategic thinking and planning",
                "Advanced prioritization methodologies",
                "Proactive conflict prevention",
                "Resource optimization techniques",
                "Customer relationship management",
                "Systems thinking and integration"
            ]
        }