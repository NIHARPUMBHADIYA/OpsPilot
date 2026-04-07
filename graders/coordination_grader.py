#!/usr/bin/env python3
"""
Coordination grader for multi-agent OpsPilot environment.

This grader evaluates how well multiple agents coordinate their actions,
detecting conflicts and measuring consistency of decisions.
"""

from typing import Dict, List, Any, Tuple, Optional
from models import MultiAgentAction, EmailAgentAction, SchedulerAgentAction


class CoordinationGrader:
    """
    Grader for evaluating coordination between multiple agents.
    
    Evaluates:
    - Conflicts between agents (e.g., both trying to handle same item)
    - Consistency of decisions (e.g., email priority matching task priority)
    - Communication efficiency (avoiding redundant actions)
    - Resource allocation conflicts
    """
    
    def __init__(self):
        """Initialize the coordination grader."""
        self.name = "coordination"
        self.description = "Evaluates coordination between multiple agents"
    
    def grade_coordination(self, 
                          multi_agent_action: MultiAgentAction,
                          observation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade coordination between agents.
        
        Args:
            multi_agent_action: Multi-agent action to evaluate
            observation_data: Current observation data for context
            
        Returns:
            Dictionary with coordination score and breakdown
        """
        if not multi_agent_action.is_multi_agent():
            # Single agent mode - perfect coordination by definition
            return {
                "coordination_score": 1.0,
                "breakdown": {
                    "conflict_penalty": 0.0,
                    "consistency_score": 1.0,
                    "efficiency_score": 1.0,
                    "communication_score": 1.0
                },
                "details": {
                    "mode": "single_agent",
                    "conflicts": [],
                    "consistency_issues": [],
                    "efficiency_issues": []
                }
            }
        
        # Multi-agent coordination evaluation
        email_agent = multi_agent_action.email_agent
        scheduler_agent = multi_agent_action.scheduler_agent
        
        # Initialize scores
        conflict_penalty = 0.0
        consistency_score = 1.0
        efficiency_score = 1.0
        communication_score = 1.0
        
        # Track issues for detailed feedback
        conflicts = []
        consistency_issues = []
        efficiency_issues = []
        
        # 1. Detect conflicts between agents
        if email_agent and scheduler_agent:
            conflict_penalty, conflicts = self._detect_conflicts(
                email_agent, scheduler_agent, observation_data
            )
        
        # 2. Evaluate consistency of decisions
        if email_agent and scheduler_agent:
            consistency_score, consistency_issues = self._evaluate_consistency(
                email_agent, scheduler_agent, observation_data
            )
        
        # 3. Evaluate efficiency (avoiding redundant actions)
        if email_agent and scheduler_agent:
            efficiency_score, efficiency_issues = self._evaluate_efficiency(
                email_agent, scheduler_agent, observation_data
            )
        
        # 4. Evaluate communication (implicit through action coordination)
        if email_agent and scheduler_agent:
            communication_score = self._evaluate_communication(
                email_agent, scheduler_agent, observation_data
            )
        
        # Calculate overall coordination score
        # Formula: base_score - conflict_penalty, weighted by other factors
        base_score = (consistency_score * 0.4 + 
                     efficiency_score * 0.3 + 
                     communication_score * 0.3)
        
        coordination_score = max(0.0, base_score - conflict_penalty)
        
        return {
            "coordination_score": round(coordination_score, 4),
            "breakdown": {
                "conflict_penalty": round(conflict_penalty, 4),
                "consistency_score": round(consistency_score, 4),
                "efficiency_score": round(efficiency_score, 4),
                "communication_score": round(communication_score, 4)
            },
            "details": {
                "mode": "multi_agent",
                "conflicts": conflicts,
                "consistency_issues": consistency_issues,
                "efficiency_issues": efficiency_issues,
                "agents_active": {
                    "email_agent": email_agent is not None,
                    "scheduler_agent": scheduler_agent is not None
                }
            }
        }
    
    def _detect_conflicts(self, 
                         email_agent: EmailAgentAction,
                         scheduler_agent: SchedulerAgentAction,
                         observation_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Detect conflicts between agents.
        
        Returns:
            Tuple of (conflict_penalty, list_of_conflicts)
        """
        conflicts = []
        penalty = 0.0
        
        # 1. Check for overlapping skip IDs (both agents skipping same item)
        email_skips = set(email_agent.skip_ids)
        scheduler_skips = set(scheduler_agent.skip_ids)
        overlapping_skips = email_skips.intersection(scheduler_skips)
        
        if overlapping_skips:
            conflicts.append(f"Both agents skipping same items: {list(overlapping_skips)}")
            penalty += 0.1 * len(overlapping_skips)
        
        # 2. Check for resource allocation conflicts
        # (e.g., email agent scheduling response time conflicting with scheduler's timeline)
        email_actions = email_agent.email_actions
        scheduling_actions = scheduler_agent.scheduling
        
        # Extract scheduled times from both agents
        email_times = []
        for action in email_actions:
            if 'estimated_time' in action:
                email_times.append(action['estimated_time'])
        
        scheduled_times = []
        for schedule in scheduling_actions:
            scheduled_times.append(schedule['scheduled_time'])
            if 'duration' in schedule:
                # Add end time
                scheduled_times.append(schedule['scheduled_time'] + schedule['duration'])
        
        # Check for time conflicts (simplified - assumes sequential processing)
        if email_times and scheduled_times:
            total_email_time = sum(email_times)
            earliest_schedule = min(scheduled_times) if scheduled_times else float('inf')
            
            if total_email_time > earliest_schedule:
                conflicts.append(f"Email processing time ({total_email_time}min) conflicts with earliest schedule ({earliest_schedule}min)")
                penalty += 0.15
        
        # 3. Check for priority conflicts
        # (e.g., email agent marking something high priority while scheduler marks it low)
        email_priorities = {}
        for action in email_actions:
            if 'priority' in action:
                email_priorities[action['email_id']] = action['priority']
        
        task_priorities = {}
        for priority in scheduler_agent.task_priorities:
            task_priorities[priority['task_id']] = priority['priority_level']
        
        # Check if any items are handled by both with conflicting priorities
        # (This is a simplified check - in practice, would need item relationship mapping)
        
        return min(penalty, 0.5), conflicts  # Cap penalty at 0.5
    
    def _evaluate_consistency(self,
                            email_agent: EmailAgentAction,
                            scheduler_agent: SchedulerAgentAction,
                            observation_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Evaluate consistency of decisions between agents.
        
        Returns:
            Tuple of (consistency_score, list_of_issues)
        """
        issues = []
        score = 1.0
        
        # 1. Check priority alignment
        # High-priority emails should correspond to high-priority tasks
        high_priority_emails = []
        for action in email_agent.email_actions:
            if action.get('priority') == 'high':
                high_priority_emails.append(action['email_id'])
        
        high_priority_tasks = []
        for priority in scheduler_agent.task_priorities:
            if priority['priority_level'] >= 8:  # High priority threshold
                high_priority_tasks.append(priority['task_id'])
        
        # Check if high-priority email handling aligns with high-priority task scheduling
        if high_priority_emails and not high_priority_tasks:
            issues.append("High-priority emails handled but no high-priority tasks scheduled")
            score -= 0.2
        elif high_priority_tasks and not high_priority_emails:
            issues.append("High-priority tasks scheduled but no high-priority emails handled")
            score -= 0.2
        
        # 2. Check urgency consistency
        # Urgent actions should be reflected in both agents' decisions
        urgent_email_actions = len([a for a in email_agent.email_actions 
                                   if a.get('action_type') in ['reply', 'escalate']])
        
        immediate_scheduling = len([s for s in scheduler_agent.scheduling 
                                  if s.get('scheduled_time', 0) <= 15])  # Within 15 minutes
        
        if urgent_email_actions > 0 and immediate_scheduling == 0:
            issues.append("Urgent email actions taken but no immediate scheduling")
            score -= 0.15
        
        # 3. Check workload balance
        # Both agents should have reasonable workloads
        email_workload = len(email_agent.email_actions)
        scheduler_workload = len(scheduler_agent.task_priorities) + len(scheduler_agent.scheduling)
        
        if email_workload > 0 and scheduler_workload == 0:
            issues.append("Email agent active but scheduler agent idle")
            score -= 0.1
        elif scheduler_workload > 0 and email_workload == 0:
            issues.append("Scheduler agent active but email agent idle")
            score -= 0.1
        
        return max(0.0, score), issues
    
    def _evaluate_efficiency(self,
                           email_agent: EmailAgentAction,
                           scheduler_agent: SchedulerAgentAction,
                           observation_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Evaluate efficiency of multi-agent coordination.
        
        Returns:
            Tuple of (efficiency_score, list_of_issues)
        """
        issues = []
        score = 1.0
        
        # 1. Check for redundant actions
        # Both agents shouldn't be handling the same items unnecessarily
        email_handled_items = set(action['email_id'] for action in email_agent.email_actions)
        scheduler_handled_items = set()
        
        for priority in scheduler_agent.task_priorities:
            scheduler_handled_items.add(priority['task_id'])
        for schedule in scheduler_agent.scheduling:
            scheduler_handled_items.add(schedule['item_id'])
        
        # This is a simplified check - in practice, would need better item relationship mapping
        
        # 2. Check for optimal division of labor
        # Email agent should focus on emails, scheduler on tasks/scheduling
        total_actions = len(email_agent.email_actions) + len(scheduler_agent.task_priorities) + len(scheduler_agent.scheduling)
        
        if total_actions == 0:
            issues.append("No actions taken by either agent")
            score -= 0.3
        
        # 3. Check for balanced workload distribution
        email_actions_count = len(email_agent.email_actions)
        scheduler_actions_count = len(scheduler_agent.task_priorities) + len(scheduler_agent.scheduling)
        
        if total_actions > 0:
            email_ratio = email_actions_count / total_actions
            scheduler_ratio = scheduler_actions_count / total_actions
            
            # Ideal ratio depends on available work, but extreme imbalances are inefficient
            if email_ratio > 0.8 or scheduler_ratio > 0.8:
                issues.append(f"Unbalanced workload: email {email_ratio:.1%}, scheduler {scheduler_ratio:.1%}")
                score -= 0.1
        
        # 4. Check skip efficiency
        # Agents should coordinate skipping to avoid both skipping everything
        total_skips = len(email_agent.skip_ids) + len(scheduler_agent.skip_ids)
        if total_skips > total_actions * 2:  # More skips than actions
            issues.append("Excessive skipping by both agents")
            score -= 0.15
        
        return max(0.0, score), issues
    
    def _evaluate_communication(self,
                              email_agent: EmailAgentAction,
                              scheduler_agent: SchedulerAgentAction,
                              observation_data: Dict[str, Any]) -> float:
        """
        Evaluate implicit communication through action coordination.
        
        Returns:
            Communication score (0.0 to 1.0)
        """
        score = 1.0
        
        # 1. Check for complementary actions
        # Good coordination shows complementary rather than conflicting actions
        email_has_actions = len(email_agent.email_actions) > 0
        scheduler_has_actions = (len(scheduler_agent.task_priorities) > 0 or 
                               len(scheduler_agent.scheduling) > 0)
        
        if email_has_actions and scheduler_has_actions:
            # Both agents active - good coordination
            score = 1.0
        elif email_has_actions or scheduler_has_actions:
            # One agent active - partial coordination
            score = 0.7
        else:
            # No agents active - poor coordination
            score = 0.3
        
        # 2. Check for strategic coordination
        # High-priority items should be handled by appropriate agent
        high_priority_email_actions = len([a for a in email_agent.email_actions 
                                         if a.get('priority') == 'high'])
        
        high_priority_task_actions = len([p for p in scheduler_agent.task_priorities 
                                        if p.get('priority_level', 0) >= 8])
        
        if high_priority_email_actions > 0 and high_priority_task_actions > 0:
            # Both handling high-priority items - excellent coordination
            score = min(1.0, score + 0.1)
        
        return score
    
    def get_coordination_insights(self, coordination_result: Dict[str, Any]) -> List[str]:
        """
        Generate actionable insights from coordination evaluation.
        
        Args:
            coordination_result: Result from grade_coordination()
            
        Returns:
            List of insight strings
        """
        insights = []
        
        if coordination_result["details"]["mode"] == "single_agent":
            insights.append("Single agent mode - no coordination issues")
            return insights
        
        score = coordination_result["coordination_score"]
        breakdown = coordination_result["breakdown"]
        details = coordination_result["details"]
        
        # Overall performance insights
        if score >= 0.9:
            insights.append("Excellent coordination between agents")
        elif score >= 0.7:
            insights.append("Good coordination with minor issues")
        elif score >= 0.5:
            insights.append("Moderate coordination - room for improvement")
        else:
            insights.append("Poor coordination - significant issues detected")
        
        # Specific issue insights
        if breakdown["conflict_penalty"] > 0.1:
            insights.append(f"Conflict penalty: {breakdown['conflict_penalty']:.2f} - agents are working against each other")
        
        if breakdown["consistency_score"] < 0.8:
            insights.append("Consistency issues - agents making conflicting priority decisions")
        
        if breakdown["efficiency_score"] < 0.8:
            insights.append("Efficiency issues - redundant or unbalanced work distribution")
        
        if breakdown["communication_score"] < 0.8:
            insights.append("Communication issues - agents not coordinating effectively")
        
        # Specific conflict insights
        if details["conflicts"]:
            insights.append(f"Detected conflicts: {'; '.join(details['conflicts'])}")
        
        # Improvement suggestions
        if score < 0.8:
            insights.append("Suggestion: Improve agent coordination through better priority alignment")
            insights.append("Suggestion: Reduce overlapping responsibilities and conflicts")
        
        return insights