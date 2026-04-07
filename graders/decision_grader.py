"""Deterministic decision grader for OpsPilot - evaluates prioritization alignment with failure mode analysis."""

from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime


class DecisionGrader:
    """Deterministic grader for decision-making quality with comprehensive failure mode detection."""
    
    def __init__(self) -> None:
        """Initialize decision grader."""
        self.grader_type = "decision"
        self.max_score = 1.0
        
        # Define priority scoring weights
        self.priority_weights = {
            "task_prioritization": 0.4,    # Most important - did agent prioritize high-importance tasks?
            "vip_email_handling": 0.35,    # Critical - did it handle VIP emails first?
            "low_value_filtering": 0.25    # Important - did it ignore low-value tasks?
        }
        
        # Define importance thresholds
        self.high_importance_threshold = 7  # Tasks with importance >= 7 are high priority
        self.low_importance_threshold = 3   # Tasks with importance <= 3 are low priority
        self.high_urgency_threshold = 8     # Emails with urgency >= 8 are high priority
        
        # Failure mode detection thresholds
        self.failure_thresholds = {
            "hallucination": 0.1,          # Any non-existent items referenced
            "poor_prioritization": 0.6,    # Task prioritization score below 60%
            "inefficient_actions": 0.5,    # Efficiency score below 50%
            "tone_failure": 0.4,           # Inappropriate responses to customer tone
            "missed_vip": 0.8,             # VIP handling score below 80%
            "resource_waste": 0.3,         # Excessive resource allocation to low-value items
            "deadline_ignore": 0.1,        # Any deadline violations
            "inconsistent_logic": 0.2      # Contradictory decisions
        }
    
    def grade(self, agent_decisions: Dict[str, Any], 
              optimal_priorities: Dict[str, Any],
              ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade decision-making quality with comprehensive failure mode analysis.
        
        Args:
            agent_decisions: Agent's prioritization decisions
                Format: {
                    "task_priorities": [{"task_id": str, "priority_level": int, "reasoning": str}],
                    "email_actions": [{"email_id": str, "action_type": str, "order": int}],
                    "ignored_items": [str]  # IDs of items the agent chose to ignore
                }
            optimal_priorities: Ground truth optimal priorities
                Format: {
                    "task_priorities": {"task_id": int},  # Optimal priority levels
                    "email_priorities": {"email_id": int},  # Optimal email priorities
                    "high_importance_tasks": [str],  # Task IDs that should be prioritized
                    "vip_emails": [str],  # Email IDs from VIP customers
                    "low_value_items": [str]  # Items that should be ignored/deprioritized
                }
            ground_truth: Additional context about items
                Format: {
                    "tasks": {"task_id": {"importance": int, "deadline": int}},
                    "emails": {"email_id": {"customer_tier": str, "urgency": int, "tone": str}}
                }
                
        Returns:
            Grading result with score between 0-1, detailed breakdown, and failure modes
        """
        if not optimal_priorities:
            return self._create_empty_result("No optimal priorities provided for comparison")
        
        # Grade each component
        task_score, task_details = self._grade_task_prioritization(
            agent_decisions.get("task_priorities", []),
            optimal_priorities.get("task_priorities", {}),
            ground_truth.get("tasks", {})
        )
        
        vip_score, vip_details = self._grade_vip_email_handling(
            agent_decisions.get("email_actions", []),
            optimal_priorities.get("vip_emails", []),
            ground_truth.get("emails", {})
        )
        
        low_value_score, low_value_details = self._grade_low_value_filtering(
            agent_decisions.get("ignored_items", []),
            agent_decisions.get("task_priorities", []),
            agent_decisions.get("email_actions", []),
            optimal_priorities.get("low_value_items", []),
            ground_truth
        )
        
        # Calculate weighted final score
        final_score = (
            task_score * self.priority_weights["task_prioritization"] +
            vip_score * self.priority_weights["vip_email_handling"] +
            low_value_score * self.priority_weights["low_value_filtering"]
        )
        
        # Detect failure modes
        failure_modes = self._detect_failure_modes(
            agent_decisions, optimal_priorities, ground_truth,
            task_score, vip_score, low_value_score, final_score
        )
        
        # Generate feedback
        feedback = self._generate_feedback(task_score, vip_score, low_value_score, final_score, failure_modes)
        
        return {
            "score": min(final_score, self.max_score),
            "feedback": feedback,
            "failure_modes": failure_modes,
            "details": {
                "component_scores": {
                    "task_prioritization": task_score,
                    "vip_email_handling": vip_score,
                    "low_value_filtering": low_value_score
                },
                "breakdown": {
                    "task_prioritization": task_details,
                    "vip_email_handling": vip_details,
                    "low_value_filtering": low_value_details
                },
                "weights_used": self.priority_weights,
                "failure_analysis": self._get_failure_analysis(failure_modes, agent_decisions, ground_truth)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _grade_task_prioritization(self, agent_priorities: List[Dict[str, Any]], 
                                  optimal_priorities: Dict[str, int],
                                  task_ground_truth: Dict[str, Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Grade how well the agent prioritized high-importance tasks."""
        if not optimal_priorities and not task_ground_truth:
            return 0.5, {"reason": "No task priority data available"}
        
        # Create agent priority mapping
        agent_priority_map = {tp["task_id"]: tp["priority_level"] for tp in agent_priorities}
        
        # Identify high-importance tasks from ground truth
        high_importance_tasks = []
        for task_id, task_info in task_ground_truth.items():
            if task_info.get("importance", 0) >= self.high_importance_threshold:
                high_importance_tasks.append(task_id)
        
        if not high_importance_tasks:
            return 0.5, {"reason": "No high-importance tasks to evaluate"}
        
        # Check if agent prioritized high-importance tasks correctly
        correctly_prioritized = 0
        priority_errors = []
        
        for task_id in high_importance_tasks:
            agent_priority = agent_priority_map.get(task_id)
            optimal_priority = optimal_priorities.get(task_id)
            task_importance = task_ground_truth.get(task_id, {}).get("importance", 0)
            
            if agent_priority is None:
                priority_errors.append({
                    "task_id": task_id,
                    "error": "not_prioritized",
                    "importance": task_importance
                })
                continue
            
            # Check if agent gave high priority (7+) to high-importance tasks
            if agent_priority >= 7:
                correctly_prioritized += 1
            else:
                priority_errors.append({
                    "task_id": task_id,
                    "error": "under_prioritized",
                    "agent_priority": agent_priority,
                    "importance": task_importance
                })
            
            # Bonus for exact match with optimal priority
            if optimal_priority and abs(agent_priority - optimal_priority) <= 1:
                correctly_prioritized += 0.2  # Bonus for close match
        
        # Calculate score
        base_score = correctly_prioritized / len(high_importance_tasks)
        
        # Penalty for prioritizing low-importance tasks too highly
        penalty = self._calculate_over_prioritization_penalty(
            agent_priorities, task_ground_truth
        )
        
        final_score = max(0.0, base_score - penalty)
        
        details = {
            "high_importance_tasks_count": len(high_importance_tasks),
            "correctly_prioritized": int(correctly_prioritized),
            "priority_errors": priority_errors,
            "over_prioritization_penalty": penalty,
            "base_score": base_score,
            "agent_priorities_count": len(agent_priorities)
        }
        
        return min(final_score, 1.0), details
    
    def _grade_vip_email_handling(self, agent_email_actions: List[Dict[str, Any]], 
                                 vip_emails: List[str],
                                 email_ground_truth: Dict[str, Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Grade how well the agent handled VIP emails first."""
        # Identify VIP emails from ground truth if not provided
        if not vip_emails:
            vip_emails = []
            for email_id, email_info in email_ground_truth.items():
                if email_info.get("customer_tier") == "vip":
                    vip_emails.append(email_id)
        
        if not vip_emails:
            return 1.0, {"reason": "No VIP emails to evaluate"}
        
        # Create action order mapping
        email_action_order = {}
        for i, action in enumerate(agent_email_actions):
            email_id = action.get("email_id")
            if email_id:
                email_action_order[email_id] = i
        
        # Check if VIP emails were handled first
        vip_handling_scores = []
        vip_handling_details = []
        
        for vip_email_id in vip_emails:
            vip_order = email_action_order.get(vip_email_id)
            
            if vip_order is None:
                # VIP email not handled at all - major penalty
                vip_handling_scores.append(0.0)
                vip_handling_details.append({
                    "email_id": vip_email_id,
                    "status": "not_handled",
                    "score": 0.0
                })
                continue
            
            # Count how many non-VIP emails were handled before this VIP email
            non_vip_before = 0
            for email_id, order in email_action_order.items():
                if (order < vip_order and 
                    email_id not in vip_emails and 
                    email_ground_truth.get(email_id, {}).get("customer_tier") != "vip"):
                    non_vip_before += 1
            
            # Score based on priority order (fewer non-VIP emails before = higher score)
            if non_vip_before == 0:
                score = 1.0  # Perfect - VIP handled first
            elif non_vip_before <= 2:
                score = 0.7  # Good - VIP handled early
            elif non_vip_before <= 4:
                score = 0.4  # Acceptable - VIP handled reasonably early
            else:
                score = 0.1  # Poor - VIP handled late
            
            vip_handling_scores.append(score)
            vip_handling_details.append({
                "email_id": vip_email_id,
                "order": vip_order,
                "non_vip_before": non_vip_before,
                "score": score,
                "status": "handled"
            })
        
        # Calculate average VIP handling score
        avg_score = sum(vip_handling_scores) / len(vip_handling_scores) if vip_handling_scores else 0.0
        
        # Bonus for appropriate action types for VIP emails
        action_type_bonus = self._calculate_vip_action_bonus(
            agent_email_actions, vip_emails, email_ground_truth
        )
        
        final_score = min(avg_score + action_type_bonus, 1.0)
        
        details = {
            "vip_emails_count": len(vip_emails),
            "vip_handling_details": vip_handling_details,
            "average_vip_score": avg_score,
            "action_type_bonus": action_type_bonus,
            "total_email_actions": len(agent_email_actions)
        }
        
        return final_score, details
    
    def _grade_low_value_filtering(self, ignored_items: List[str],
                                  task_priorities: List[Dict[str, Any]],
                                  email_actions: List[Dict[str, Any]],
                                  optimal_low_value_items: List[str],
                                  ground_truth: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Grade how well the agent ignored or deprioritized low-value tasks."""
        # Identify low-value items from ground truth
        low_value_tasks = []
        low_value_emails = []
        
        # Find low-importance tasks
        for task_id, task_info in ground_truth.get("tasks", {}).items():
            if task_info.get("importance", 10) <= self.low_importance_threshold:
                low_value_tasks.append(task_id)
        
        # Find low-urgency emails from free customers
        for email_id, email_info in ground_truth.get("emails", {}).items():
            if (email_info.get("customer_tier") == "free" and 
                email_info.get("urgency", 10) <= 4):
                low_value_emails.append(email_id)
        
        all_low_value_items = low_value_tasks + low_value_emails + optimal_low_value_items
        
        if not all_low_value_items:
            return 1.0, {"reason": "No low-value items to evaluate"}
        
        # Check how agent handled low-value items
        correctly_filtered = 0
        filtering_details = []
        
        # Create sets for quick lookup
        handled_tasks = {tp["task_id"] for tp in task_priorities}
        handled_emails = {ea["email_id"] for ea in email_actions}
        ignored_set = set(ignored_items)
        
        for item_id in all_low_value_items:
            is_task = item_id in ground_truth.get("tasks", {})
            is_email = item_id in ground_truth.get("emails", {})
            
            if item_id in ignored_set:
                # Correctly ignored
                correctly_filtered += 1
                filtering_details.append({
                    "item_id": item_id,
                    "type": "task" if is_task else "email",
                    "status": "correctly_ignored",
                    "score": 1.0
                })
            elif is_task and item_id in handled_tasks:
                # Task was prioritized - check if given low priority
                task_priority = next((tp["priority_level"] for tp in task_priorities 
                                    if tp["task_id"] == item_id), None)
                if task_priority and task_priority <= 3:
                    # Given low priority - acceptable
                    correctly_filtered += 0.7
                    filtering_details.append({
                        "item_id": item_id,
                        "type": "task",
                        "status": "low_priority_assigned",
                        "priority": task_priority,
                        "score": 0.7
                    })
                else:
                    # Given high priority - error
                    filtering_details.append({
                        "item_id": item_id,
                        "type": "task",
                        "status": "over_prioritized",
                        "priority": task_priority,
                        "score": 0.0
                    })
            elif is_email and item_id in handled_emails:
                # Email was handled - check action type
                email_action = next((ea for ea in email_actions if ea["email_id"] == item_id), None)
                action_type = email_action.get("action_type") if email_action else None
                
                if action_type in ["defer", "archive"]:
                    # Appropriate low-priority action
                    correctly_filtered += 0.8
                    filtering_details.append({
                        "item_id": item_id,
                        "type": "email",
                        "status": "appropriate_action",
                        "action": action_type,
                        "score": 0.8
                    })
                else:
                    # Inappropriate high-priority action
                    filtering_details.append({
                        "item_id": item_id,
                        "type": "email",
                        "status": "inappropriate_action",
                        "action": action_type,
                        "score": 0.2
                    })
            else:
                # Item not handled at all - could be good (ignored) or bad (missed)
                correctly_filtered += 0.5  # Neutral score
                filtering_details.append({
                    "item_id": item_id,
                    "type": "task" if is_task else "email",
                    "status": "not_handled",
                    "score": 0.5
                })
        
        # Calculate final score
        final_score = correctly_filtered / len(all_low_value_items) if all_low_value_items else 1.0
        
        details = {
            "low_value_items_count": len(all_low_value_items),
            "low_value_tasks": low_value_tasks,
            "low_value_emails": low_value_emails,
            "correctly_filtered": correctly_filtered,
            "filtering_details": filtering_details,
            "ignored_items_count": len(ignored_items)
        }
        
        return min(final_score, 1.0), details
    
    def _calculate_over_prioritization_penalty(self, agent_priorities: List[Dict[str, Any]],
                                             task_ground_truth: Dict[str, Dict[str, Any]]) -> float:
        """Calculate penalty for giving high priority to low-importance tasks."""
        penalty = 0.0
        
        for task_priority in agent_priorities:
            task_id = task_priority["task_id"]
            agent_priority = task_priority["priority_level"]
            task_importance = task_ground_truth.get(task_id, {}).get("importance", 5)
            
            # Penalty if agent gave high priority (8+) to low-importance task (≤3)
            if agent_priority >= 8 and task_importance <= self.low_importance_threshold:
                penalty += 0.1
            # Smaller penalty for medium mismatch
            elif agent_priority >= 7 and task_importance <= 4:
                penalty += 0.05
        
        return min(penalty, 0.3)  # Cap penalty at 0.3
    
    def _calculate_vip_action_bonus(self, agent_email_actions: List[Dict[str, Any]],
                                   vip_emails: List[str],
                                   email_ground_truth: Dict[str, Dict[str, Any]]) -> float:
        """Calculate bonus for using appropriate action types for VIP emails."""
        bonus = 0.0
        vip_actions_count = 0
        
        for action in agent_email_actions:
            email_id = action.get("email_id")
            action_type = action.get("action_type")
            
            if email_id in vip_emails:
                vip_actions_count += 1
                # VIP emails should get "reply" or "escalate" actions
                if action_type in ["reply", "escalate"]:
                    bonus += 0.05  # Small bonus per appropriate VIP action
        
        return min(bonus, 0.1)  # Cap bonus at 0.1
    
    def _detect_failure_modes(self, agent_decisions: Dict[str, Any], 
                             optimal_priorities: Dict[str, Any],
                             ground_truth: Dict[str, Any],
                             task_score: float, vip_score: float, 
                             low_value_score: float, final_score: float) -> List[str]:
        """
        Detect various failure modes in agent decision-making.
        
        Returns:
            List of detected failure mode strings
        """
        failure_modes = []
        
        # 1. Hallucination Detection
        if self._detect_hallucination(agent_decisions, ground_truth):
            failure_modes.append("hallucination")
        
        # 2. Poor Prioritization
        if task_score < self.failure_thresholds["poor_prioritization"]:
            failure_modes.append("poor_prioritization")
        
        # 3. Inefficient Actions
        if self._detect_inefficient_actions(agent_decisions, ground_truth):
            failure_modes.append("inefficient_actions")
        
        # 4. Tone Failure
        if self._detect_tone_failure(agent_decisions, ground_truth):
            failure_modes.append("tone_failure")
        
        # 5. Missed VIP
        if vip_score < self.failure_thresholds["missed_vip"]:
            failure_modes.append("missed_vip")
        
        # 6. Resource Waste
        if self._detect_resource_waste(agent_decisions, ground_truth):
            failure_modes.append("resource_waste")
        
        # 7. Deadline Ignore
        if self._detect_deadline_ignore(agent_decisions, ground_truth):
            failure_modes.append("deadline_ignore")
        
        # 8. Inconsistent Logic
        if self._detect_inconsistent_logic(agent_decisions, ground_truth):
            failure_modes.append("inconsistent_logic")
        
        return failure_modes
    
    def _detect_hallucination(self, agent_decisions: Dict[str, Any], 
                             ground_truth: Dict[str, Any]) -> bool:
        """Detect if agent referenced non-existent items."""
        valid_task_ids = set(ground_truth.get("tasks", {}).keys())
        valid_email_ids = set(ground_truth.get("emails", {}).keys())
        
        # Check task priorities for non-existent tasks
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            if task_id and task_id not in valid_task_ids:
                return True
        
        # Check email actions for non-existent emails
        for email_action in agent_decisions.get("email_actions", []):
            email_id = email_action.get("email_id")
            if email_id and email_id not in valid_email_ids:
                return True
        
        # Check ignored items for non-existent items
        all_valid_ids = valid_task_ids | valid_email_ids
        for ignored_id in agent_decisions.get("ignored_items", []):
            if ignored_id and ignored_id not in all_valid_ids:
                return True
        
        return False
    
    def _detect_inefficient_actions(self, agent_decisions: Dict[str, Any], 
                                   ground_truth: Dict[str, Any]) -> bool:
        """Detect inefficient action patterns."""
        # Check for excessive actions on low-value items
        low_value_action_count = 0
        total_actions = 0
        
        # Count actions on low-importance tasks
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            priority_level = task_priority.get("priority_level", 0)
            task_info = ground_truth.get("tasks", {}).get(task_id, {})
            importance = task_info.get("importance", 5)
            
            total_actions += 1
            if importance <= self.low_importance_threshold and priority_level >= 7:
                low_value_action_count += 1
        
        # Count actions on low-urgency emails from free customers
        for email_action in agent_decisions.get("email_actions", []):
            email_id = email_action.get("email_id")
            action_type = email_action.get("action_type")
            email_info = ground_truth.get("emails", {}).get(email_id, {})
            
            total_actions += 1
            if (email_info.get("customer_tier") == "free" and 
                email_info.get("urgency", 10) <= 4 and
                action_type in ["reply", "escalate"]):
                low_value_action_count += 1
        
        # Inefficient if >50% of actions are on low-value items
        if total_actions > 0:
            inefficiency_ratio = low_value_action_count / total_actions
            return inefficiency_ratio > self.failure_thresholds["inefficient_actions"]
        
        return False
    
    def _detect_tone_failure(self, agent_decisions: Dict[str, Any], 
                            ground_truth: Dict[str, Any]) -> bool:
        """Detect inappropriate responses to customer tone."""
        tone_failures = 0
        total_tone_sensitive_actions = 0
        
        for email_action in agent_decisions.get("email_actions", []):
            email_id = email_action.get("email_id")
            action_type = email_action.get("action_type")
            email_info = ground_truth.get("emails", {}).get(email_id, {})
            tone = email_info.get("tone", "")
            customer_tier = email_info.get("customer_tier", "")
            urgency = email_info.get("urgency", 5)
            
            # Check for tone-sensitive situations
            if tone in ["angry", "sarcastic", "mixed_intent"] or customer_tier == "vip" or urgency >= 8:
                total_tone_sensitive_actions += 1
                
                # Inappropriate actions for sensitive situations
                if tone == "angry" and action_type in ["defer", "archive"]:
                    tone_failures += 1
                elif customer_tier == "vip" and action_type in ["defer", "archive"]:
                    tone_failures += 1
                elif urgency >= 8 and action_type in ["defer", "archive"]:
                    tone_failures += 1
                elif tone == "sarcastic" and action_type == "archive":
                    tone_failures += 1
        
        # Tone failure if >40% of tone-sensitive actions are inappropriate
        if total_tone_sensitive_actions > 0:
            failure_ratio = tone_failures / total_tone_sensitive_actions
            return failure_ratio > self.failure_thresholds["tone_failure"]
        
        return False
    
    def _detect_resource_waste(self, agent_decisions: Dict[str, Any], 
                              ground_truth: Dict[str, Any]) -> bool:
        """Detect excessive resource allocation to low-value items."""
        high_priority_low_value_count = 0
        total_priorities = len(agent_decisions.get("task_priorities", []))
        
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            priority_level = task_priority.get("priority_level", 0)
            task_info = ground_truth.get("tasks", {}).get(task_id, {})
            importance = task_info.get("importance", 5)
            
            # High priority (8+) given to low importance (≤3) tasks
            if priority_level >= 8 and importance <= self.low_importance_threshold:
                high_priority_low_value_count += 1
        
        # Resource waste if >30% of priorities are misallocated
        if total_priorities > 0:
            waste_ratio = high_priority_low_value_count / total_priorities
            return waste_ratio > self.failure_thresholds["resource_waste"]
        
        return False
    
    def _detect_deadline_ignore(self, agent_decisions: Dict[str, Any], 
                               ground_truth: Dict[str, Any]) -> bool:
        """Detect ignoring of urgent deadlines."""
        urgent_tasks_ignored = 0
        
        # Check if urgent deadline tasks are not prioritized
        for task_id, task_info in ground_truth.get("tasks", {}).items():
            deadline = task_info.get("deadline", 100)
            importance = task_info.get("importance", 5)
            
            # Task with urgent deadline (≤10 time units) and high importance
            if deadline <= 10 and importance >= 7:
                # Check if agent prioritized this task
                agent_priority = None
                for task_priority in agent_decisions.get("task_priorities", []):
                    if task_priority.get("task_id") == task_id:
                        agent_priority = task_priority.get("priority_level", 0)
                        break
                
                # If not prioritized or given low priority, it's ignored
                if agent_priority is None or agent_priority < 7:
                    urgent_tasks_ignored += 1
        
        # Any urgent deadline ignored is a failure
        return urgent_tasks_ignored > 0
    
    def _detect_inconsistent_logic(self, agent_decisions: Dict[str, Any], 
                                  ground_truth: Dict[str, Any]) -> bool:
        """Detect contradictory or inconsistent decisions."""
        inconsistencies = 0
        
        # Check for priority inconsistencies
        task_priorities = agent_decisions.get("task_priorities", [])
        
        for i, task1 in enumerate(task_priorities):
            task1_id = task1.get("task_id")
            task1_priority = task1.get("priority_level", 0)
            task1_info = ground_truth.get("tasks", {}).get(task1_id, {})
            task1_importance = task1_info.get("importance", 5)
            task1_deadline = task1_info.get("deadline", 100)
            
            for j, task2 in enumerate(task_priorities[i+1:], i+1):
                task2_id = task2.get("task_id")
                task2_priority = task2.get("priority_level", 0)
                task2_info = ground_truth.get("tasks", {}).get(task2_id, {})
                task2_importance = task2_info.get("importance", 5)
                task2_deadline = task2_info.get("deadline", 100)
                
                # Inconsistency: Lower importance task gets higher priority
                if (task1_importance > task2_importance + 2 and 
                    task1_priority < task2_priority - 2):
                    inconsistencies += 1
                
                # Inconsistency: More urgent deadline gets lower priority
                if (task1_deadline < task2_deadline - 20 and 
                    task1_priority < task2_priority - 2):
                    inconsistencies += 1
        
        # Check for email action inconsistencies
        email_actions = agent_decisions.get("email_actions", [])
        vip_emails = []
        free_emails = []
        
        for email_action in email_actions:
            email_id = email_action.get("email_id")
            action_type = email_action.get("action_type")
            email_info = ground_truth.get("emails", {}).get(email_id, {})
            customer_tier = email_info.get("customer_tier", "")
            
            if customer_tier == "vip":
                vip_emails.append((email_id, action_type))
            elif customer_tier == "free":
                free_emails.append((email_id, action_type))
        
        # Inconsistency: Free customer gets better treatment than VIP
        for vip_email_id, vip_action in vip_emails:
            for free_email_id, free_action in free_emails:
                if (vip_action in ["defer", "archive"] and 
                    free_action in ["reply", "escalate"]):
                    inconsistencies += 1
        
        # Inconsistent if >20% of comparisons show inconsistency
        total_comparisons = len(task_priorities) * (len(task_priorities) - 1) // 2
        total_comparisons += len(vip_emails) * len(free_emails)
        
        if total_comparisons > 0:
            inconsistency_ratio = inconsistencies / total_comparisons
            return inconsistency_ratio > self.failure_thresholds["inconsistent_logic"]
        
        return False
    
    def _get_failure_analysis(self, failure_modes: List[str], 
                             agent_decisions: Dict[str, Any],
                             ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed analysis of detected failure modes."""
        analysis = {}
        
        for failure_mode in failure_modes:
            if failure_mode == "hallucination":
                analysis[failure_mode] = self._analyze_hallucination(agent_decisions, ground_truth)
            elif failure_mode == "poor_prioritization":
                analysis[failure_mode] = self._analyze_poor_prioritization(agent_decisions, ground_truth)
            elif failure_mode == "inefficient_actions":
                analysis[failure_mode] = self._analyze_inefficient_actions(agent_decisions, ground_truth)
            elif failure_mode == "tone_failure":
                analysis[failure_mode] = self._analyze_tone_failure(agent_decisions, ground_truth)
            elif failure_mode == "missed_vip":
                analysis[failure_mode] = self._analyze_missed_vip(agent_decisions, ground_truth)
            elif failure_mode == "resource_waste":
                analysis[failure_mode] = self._analyze_resource_waste(agent_decisions, ground_truth)
            elif failure_mode == "deadline_ignore":
                analysis[failure_mode] = self._analyze_deadline_ignore(agent_decisions, ground_truth)
            elif failure_mode == "inconsistent_logic":
                analysis[failure_mode] = self._analyze_inconsistent_logic(agent_decisions, ground_truth)
        
        return analysis
    
    def _analyze_hallucination(self, agent_decisions: Dict[str, Any], 
                              ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze hallucination failures."""
        valid_task_ids = set(ground_truth.get("tasks", {}).keys())
        valid_email_ids = set(ground_truth.get("emails", {}).keys())
        hallucinated_items = []
        
        # Check for non-existent task references
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            if task_id and task_id not in valid_task_ids:
                hallucinated_items.append({
                    "type": "task",
                    "id": task_id,
                    "context": "task_priorities"
                })
        
        # Check for non-existent email references
        for email_action in agent_decisions.get("email_actions", []):
            email_id = email_action.get("email_id")
            if email_id and email_id not in valid_email_ids:
                hallucinated_items.append({
                    "type": "email",
                    "id": email_id,
                    "context": "email_actions"
                })
        
        return {
            "description": "Agent referenced non-existent items",
            "hallucinated_items": hallucinated_items,
            "severity": "high" if len(hallucinated_items) > 2 else "medium"
        }
    
    def _analyze_poor_prioritization(self, agent_decisions: Dict[str, Any], 
                                    ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze poor prioritization patterns."""
        priority_errors = []
        
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            agent_priority = task_priority.get("priority_level", 0)
            task_info = ground_truth.get("tasks", {}).get(task_id, {})
            importance = task_info.get("importance", 5)
            
            # High importance task given low priority
            if importance >= 8 and agent_priority <= 4:
                priority_errors.append({
                    "task_id": task_id,
                    "error_type": "under_prioritized",
                    "importance": importance,
                    "agent_priority": agent_priority
                })
            # Low importance task given high priority
            elif importance <= 3 and agent_priority >= 8:
                priority_errors.append({
                    "task_id": task_id,
                    "error_type": "over_prioritized",
                    "importance": importance,
                    "agent_priority": agent_priority
                })
        
        return {
            "description": "Significant misalignment between task importance and assigned priorities",
            "priority_errors": priority_errors,
            "error_count": len(priority_errors)
        }
    
    def _analyze_inefficient_actions(self, agent_decisions: Dict[str, Any], 
                                    ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inefficient action patterns."""
        inefficient_actions = []
        
        # Check task priorities
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            priority_level = task_priority.get("priority_level", 0)
            task_info = ground_truth.get("tasks", {}).get(task_id, {})
            importance = task_info.get("importance", 5)
            
            if importance <= self.low_importance_threshold and priority_level >= 7:
                inefficient_actions.append({
                    "type": "task",
                    "id": task_id,
                    "issue": "high_priority_low_value",
                    "importance": importance,
                    "priority": priority_level
                })
        
        # Check email actions
        for email_action in agent_decisions.get("email_actions", []):
            email_id = email_action.get("email_id")
            action_type = email_action.get("action_type")
            email_info = ground_truth.get("emails", {}).get(email_id, {})
            
            if (email_info.get("customer_tier") == "free" and 
                email_info.get("urgency", 10) <= 4 and
                action_type in ["reply", "escalate"]):
                inefficient_actions.append({
                    "type": "email",
                    "id": email_id,
                    "issue": "excessive_attention_low_value",
                    "customer_tier": email_info.get("customer_tier"),
                    "urgency": email_info.get("urgency"),
                    "action": action_type
                })
        
        return {
            "description": "Excessive resources allocated to low-value items",
            "inefficient_actions": inefficient_actions,
            "efficiency_score": max(0, 1 - len(inefficient_actions) * 0.2)
        }
    
    def _analyze_tone_failure(self, agent_decisions: Dict[str, Any], 
                             ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tone handling failures."""
        tone_failures = []
        
        for email_action in agent_decisions.get("email_actions", []):
            email_id = email_action.get("email_id")
            action_type = email_action.get("action_type")
            email_info = ground_truth.get("emails", {}).get(email_id, {})
            tone = email_info.get("tone", "")
            
            failure_reason = None
            if tone == "angry" and action_type in ["defer", "archive"]:
                failure_reason = "ignored_angry_customer"
            elif tone == "sarcastic" and action_type == "archive":
                failure_reason = "dismissed_sarcastic_feedback"
            elif email_info.get("customer_tier") == "vip" and action_type in ["defer", "archive"]:
                failure_reason = "inappropriate_vip_handling"
            
            if failure_reason:
                tone_failures.append({
                    "email_id": email_id,
                    "tone": tone,
                    "action": action_type,
                    "failure_reason": failure_reason,
                    "customer_tier": email_info.get("customer_tier")
                })
        
        return {
            "description": "Inappropriate responses to customer tone and context",
            "tone_failures": tone_failures,
            "failure_count": len(tone_failures)
        }
    
    def _analyze_missed_vip(self, agent_decisions: Dict[str, Any], 
                           ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze VIP customer handling failures."""
        vip_issues = []
        
        # Find VIP emails
        vip_emails = []
        for email_id, email_info in ground_truth.get("emails", {}).items():
            if email_info.get("customer_tier") == "vip":
                vip_emails.append(email_id)
        
        # Check how VIP emails were handled
        email_actions = {ea["email_id"]: ea for ea in agent_decisions.get("email_actions", [])}
        
        for vip_email_id in vip_emails:
            if vip_email_id not in email_actions:
                vip_issues.append({
                    "email_id": vip_email_id,
                    "issue": "not_handled",
                    "severity": "high"
                })
            else:
                action = email_actions[vip_email_id]
                if action.get("action_type") in ["defer", "archive"]:
                    vip_issues.append({
                        "email_id": vip_email_id,
                        "issue": "inappropriate_action",
                        "action": action.get("action_type"),
                        "severity": "medium"
                    })
        
        return {
            "description": "Inadequate handling of VIP customer communications",
            "vip_issues": vip_issues,
            "vip_emails_total": len(vip_emails),
            "issues_count": len(vip_issues)
        }
    
    def _analyze_resource_waste(self, agent_decisions: Dict[str, Any], 
                               ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource waste patterns."""
        waste_instances = []
        
        for task_priority in agent_decisions.get("task_priorities", []):
            task_id = task_priority.get("task_id")
            priority_level = task_priority.get("priority_level", 0)
            task_info = ground_truth.get("tasks", {}).get(task_id, {})
            importance = task_info.get("importance", 5)
            
            if priority_level >= 8 and importance <= self.low_importance_threshold:
                waste_instances.append({
                    "task_id": task_id,
                    "waste_type": "high_priority_low_importance",
                    "priority_assigned": priority_level,
                    "actual_importance": importance,
                    "waste_severity": priority_level - importance
                })
        
        return {
            "description": "Inefficient allocation of attention and resources",
            "waste_instances": waste_instances,
            "total_waste_score": sum(wi.get("waste_severity", 0) for wi in waste_instances)
        }
    
    def _analyze_deadline_ignore(self, agent_decisions: Dict[str, Any], 
                                ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze deadline ignorance patterns."""
        deadline_violations = []
        
        for task_id, task_info in ground_truth.get("tasks", {}).items():
            deadline = task_info.get("deadline", 100)
            importance = task_info.get("importance", 5)
            
            if deadline <= 10 and importance >= 7:  # Urgent and important
                # Check if agent prioritized this task
                agent_priority = None
                for task_priority in agent_decisions.get("task_priorities", []):
                    if task_priority.get("task_id") == task_id:
                        agent_priority = task_priority.get("priority_level", 0)
                        break
                
                if agent_priority is None:
                    deadline_violations.append({
                        "task_id": task_id,
                        "violation_type": "not_prioritized",
                        "deadline": deadline,
                        "importance": importance
                    })
                elif agent_priority < 7:
                    deadline_violations.append({
                        "task_id": task_id,
                        "violation_type": "under_prioritized",
                        "deadline": deadline,
                        "importance": importance,
                        "agent_priority": agent_priority
                    })
        
        return {
            "description": "Failed to prioritize tasks with urgent deadlines",
            "deadline_violations": deadline_violations,
            "violation_count": len(deadline_violations)
        }
    
    def _analyze_inconsistent_logic(self, agent_decisions: Dict[str, Any], 
                                   ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze logical inconsistencies in decisions."""
        inconsistencies = []
        
        # Check task priority inconsistencies
        task_priorities = agent_decisions.get("task_priorities", [])
        
        for i, task1 in enumerate(task_priorities):
            for j, task2 in enumerate(task_priorities[i+1:], i+1):
                task1_id = task1.get("task_id")
                task2_id = task2.get("task_id")
                task1_priority = task1.get("priority_level", 0)
                task2_priority = task2.get("priority_level", 0)
                
                task1_info = ground_truth.get("tasks", {}).get(task1_id, {})
                task2_info = ground_truth.get("tasks", {}).get(task2_id, {})
                
                task1_importance = task1_info.get("importance", 5)
                task2_importance = task2_info.get("importance", 5)
                
                # Logical inconsistency: much less important task gets higher priority
                if (task1_importance > task2_importance + 3 and 
                    task1_priority < task2_priority - 2):
                    inconsistencies.append({
                        "type": "priority_importance_mismatch",
                        "task1": task1_id,
                        "task2": task2_id,
                        "task1_importance": task1_importance,
                        "task2_importance": task2_importance,
                        "task1_priority": task1_priority,
                        "task2_priority": task2_priority
                    })
        
        return {
            "description": "Contradictory or illogical decision patterns",
            "inconsistencies": inconsistencies,
            "inconsistency_count": len(inconsistencies)
        }
    
    def _generate_feedback(self, task_score: float, vip_score: float, 
                          low_value_score: float, final_score: float, 
                          failure_modes: List[str]) -> str:
        """Generate detailed feedback based on component scores and failure modes."""
        feedback_parts = []
        
        # Overall assessment
        if final_score >= 0.9:
            feedback_parts.append("Excellent prioritization decisions!")
        elif final_score >= 0.8:
            feedback_parts.append("Very good prioritization with minor areas for improvement.")
        elif final_score >= 0.7:
            feedback_parts.append("Good prioritization but could be optimized further.")
        elif final_score >= 0.6:
            feedback_parts.append("Acceptable prioritization with several improvement areas.")
        else:
            feedback_parts.append("Poor prioritization decisions requiring significant improvement.")
        
        # Failure mode specific feedback
        if failure_modes:
            feedback_parts.append(f"Critical issues detected: {', '.join(failure_modes)}.")
            
            if "hallucination" in failure_modes:
                feedback_parts.append("Agent referenced non-existent items - verify input validation.")
            
            if "poor_prioritization" in failure_modes:
                feedback_parts.append("Significant misalignment between task importance and assigned priorities.")
            
            if "inefficient_actions" in failure_modes:
                feedback_parts.append("Excessive resources allocated to low-value items.")
            
            if "tone_failure" in failure_modes:
                feedback_parts.append("Inappropriate responses to customer tone and context.")
            
            if "missed_vip" in failure_modes:
                feedback_parts.append("VIP customers not given appropriate priority and attention.")
            
            if "resource_waste" in failure_modes:
                feedback_parts.append("High-priority resources wasted on low-importance tasks.")
            
            if "deadline_ignore" in failure_modes:
                feedback_parts.append("Critical deadlines ignored or under-prioritized.")
            
            if "inconsistent_logic" in failure_modes:
                feedback_parts.append("Contradictory decision patterns detected.")
        
        # Component-specific feedback (only if no major failures)
        if not failure_modes or len(failure_modes) <= 2:
            if task_score < 0.7:
                feedback_parts.append("Focus on prioritizing high-importance tasks more effectively.")
            
            if vip_score < 0.8:
                feedback_parts.append("Improve VIP customer handling by addressing their emails first.")
            
            if low_value_score < 0.7:
                feedback_parts.append("Better filter out low-value tasks and emails to focus on important work.")
        
        # Strengths (only if performance is reasonable)
        if final_score >= 0.6 and not failure_modes:
            best_component = max([
                ("task prioritization", task_score),
                ("VIP email handling", vip_score),
                ("low-value filtering", low_value_score)
            ], key=lambda x: x[1])
            
            if best_component[1] >= 0.8:
                feedback_parts.append(f"Strong performance in {best_component[0]}.")
        
        return " ".join(feedback_parts)
    
    def _create_empty_result(self, reason: str) -> Dict[str, Any]:
        """Create result for cases with insufficient data."""
        return {
            "score": 0.5,  # Neutral score when can't evaluate
            "feedback": f"Decision grading limited: {reason}",
            "failure_modes": [],  # No failure modes detected due to insufficient data
            "details": {
                "error": reason,
                "component_scores": {
                    "task_prioritization": 0.5,
                    "vip_email_handling": 0.5,
                    "low_value_filtering": 0.5
                },
                "failure_analysis": {}
            },
            "timestamp": datetime.now().isoformat()
        }