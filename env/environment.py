"""Environment configuration and OpsPilot gym-like environment."""

import os
import random
import copy
from typing import Optional, Dict, Any, Tuple, Union
from pydantic import BaseModel, Field

from models import Observation, Action, Reward, MultiAgentAction
from env.state import StateManager
from graders.email_grader import EmailGrader
from graders.response_grader import ResponseGrader
from graders.decision_grader import DecisionGrader
from graders.scheduling_grader import SchedulingGrader
from graders.final_grader import FinalGrader
from graders.coordination_grader import CoordinationGrader


class Environment(BaseModel):
    """Environment configuration with deterministic behavior."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=False)
    
    # Random seed for deterministic behavior
    random_seed: int = Field(default=42)
    
    # Database configuration (if needed)
    database_url: Optional[str] = Field(default=None)
    
    def __init__(self, **kwargs):
        """Initialize environment with environment variables."""
        # Load from environment variables
        env_data = {
            'api_host': os.getenv('API_HOST', '0.0.0.0'),
            'api_port': int(os.getenv('API_PORT', '8000')),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'random_seed': int(os.getenv('RANDOM_SEED', '42')),
            'database_url': os.getenv('DATABASE_URL')
        }
        
        # Override with any provided kwargs
        env_data.update(kwargs)
        
        super().__init__(**env_data)
        
        # Set random seed for deterministic behavior
        random.seed(self.random_seed)


class OpsPilotEnv:
    """
    Gym-like environment for OpsPilot operations.
    
    Provides a standardized interface for training and evaluating agents
    with deterministic transitions and comprehensive reward computation.
    """
    
    def __init__(self, 
                 max_steps: int = 50,
                 initial_emails: int = 3,
                 initial_tasks: int = 3,
                 initial_events: int = 2,
                 random_seed: Optional[int] = None):
        """
        Initialize OpsPilot environment.
        
        Args:
            max_steps: Maximum steps per episode
            initial_emails: Number of emails to generate at start
            initial_tasks: Number of tasks to generate at start
            initial_events: Number of calendar events to generate at start
            random_seed: Random seed for deterministic behavior
        """
        self.max_steps = max_steps
        self.initial_emails = initial_emails
        self.initial_tasks = initial_tasks
        self.initial_events = initial_events
        self.random_seed = random_seed or 42
        
        # Initialize state manager
        self.state_manager = StateManager(random_seed=self.random_seed)
        
        # Initialize graders for reward computation
        self.email_grader = EmailGrader()
        self.response_grader = ResponseGrader()
        self.decision_grader = DecisionGrader()
        self.scheduling_grader = SchedulingGrader()
        self.final_grader = FinalGrader()
        
        # Episode tracking
        self.current_step = 0
        self.episode_count = 0
        self.total_reward = 0.0
        self.done = False
        
        # Action history for analysis
        self.episode_actions = []
        self.episode_rewards = []
        
    def reset(self, seed: Optional[int] = None) -> Observation:
        """
        Reset environment to initial state.
        
        Args:
            seed: Optional seed override for this episode
            
        Returns:
            Initial observation
        """
        # Update seed if provided
        if seed is not None:
            self.random_seed = seed
            random.seed(seed)
        
        # Reset state manager
        self.state_manager.reset_state()
        self.state_manager.random_seed = self.random_seed
        random.seed(self.random_seed)
        
        # Reset episode tracking
        self.current_step = 0
        self.total_reward = 0.0
        self.done = False
        self.episode_actions.clear()
        self.episode_rewards.clear()
        
        # Generate initial data
        self._generate_initial_data()
        
        # Increment episode count
        self.episode_count += 1
        
        # Return initial observation
        return self.state_manager.get_current_observation(
            include_history=True,
            max_history_items=10
        )
    
    def step(self, action: Union[Action, MultiAgentAction]) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to execute (single-agent Action or multi-agent MultiAgentAction)
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")
        
        # Handle both single-agent and multi-agent actions
        if isinstance(action, MultiAgentAction):
            # Multi-agent mode
            legacy_action = action.to_legacy_action()
            is_multi_agent = action.is_multi_agent()
        else:
            # Single-agent mode (backward compatibility)
            legacy_action = action
            is_multi_agent = False
        
        # Increment step counter
        self.current_step += 1
        
        # Update state manager's current step for delayed consequences
        self.state_manager.current_step = self.current_step
        
        # Apply action and get base reward from state manager (includes delayed consequences)
        base_reward = self.state_manager.process_action(legacy_action)
        
        # Compute comprehensive reward using graders
        comprehensive_reward = self._compute_comprehensive_reward(legacy_action, base_reward, action if is_multi_agent else None)
        
        # Update total reward
        self.total_reward += comprehensive_reward.score
        
        # Simulate consequences and time passage
        self._simulate_step_consequences()
        
        # Check if episode is done
        self.done = self._check_episode_done()
        
        # Store action and reward for analysis
        if is_multi_agent:
            self.episode_actions.append(action.model_dump())
        else:
            self.episode_actions.append(legacy_action.model_dump())
        self.episode_rewards.append(comprehensive_reward.model_dump())
        
        # Get updated observation
        observation = self.state_manager.get_current_observation(
            include_history=True,
            max_history_items=10
        )
        
        # Prepare info dictionary with explainability
        info = self._get_step_info()
        
        # Generate decision outcome explanation
        explanation = self._generate_decision_explanation(legacy_action, comprehensive_reward)
        info["explanation"] = explanation
        
        # Add delayed consequences information
        info["delayed_consequences"] = self.state_manager.get_delayed_consequences_summary()
        
        # Add multi-agent coordination info if applicable
        if is_multi_agent:
            info["multi_agent"] = {
                "mode": "multi_agent",
                "coordination_score": comprehensive_reward.breakdown.get("coordination_score", 1.0),
                "agents_active": {
                    "email_agent": action.email_agent is not None,
                    "scheduler_agent": action.scheduler_agent is not None
                }
            }
        else:
            info["multi_agent"] = {
                "mode": "single_agent",
                "coordination_score": 1.0
            }
        
        return observation, comprehensive_reward, self.done, info
    
    def state(self) -> Dict[str, Any]:
        """
        Return full hidden state for analysis and debugging.
        
        Returns:
            Complete state information including ground truth
        """
        return {
            # Episode information
            "episode_count": self.episode_count,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "done": self.done,
            "total_reward": self.total_reward,
            
            # State manager information
            "current_time": self.state_manager.current_time,
            "time_remaining": self.state_manager.time_remaining,
            "energy_budget": self.state_manager.energy_budget,
            
            # Items in state
            "emails": {eid: email.model_dump() for eid, email in self.state_manager.emails.items()},
            "tasks": {tid: task.model_dump() for tid, task in self.state_manager.tasks.items()},
            "calendar_events": {eid: event.model_dump() for eid, event in self.state_manager.calendar_events.items()},
            
            # Ground truth (hidden from agent)
            "ground_truth": {
                "email_labels": self.state_manager.ground_truth.correct_email_labels,
                "ideal_responses": self.state_manager.ground_truth.ideal_responses,
                "optimal_priorities": self.state_manager.ground_truth.optimal_priorities,
                "task_dependencies": self.state_manager.ground_truth.task_dependencies,
                "valid_schedules": self.state_manager.ground_truth.valid_schedules,
                "expected_completion_times": self.state_manager.ground_truth.expected_completion_times,
                "energy_costs": self.state_manager.ground_truth.energy_costs
            },
            
            # Consequences
            "pending_consequences": [c.__dict__ for c in self.state_manager.pending_consequences],
            "processed_consequences": [c.__dict__ for c in self.state_manager.processed_consequences],
            
            # Performance metrics
            "performance_metrics": self.state_manager.performance_metrics.copy(),
            
            # Episode history
            "action_history": self.episode_actions.copy(),
            "reward_history": self.episode_rewards.copy(),
            
            # Random seed for reproducibility
            "random_seed": self.random_seed
        }
    
    def _generate_initial_data(self) -> None:
        """Generate initial emails, tasks, and calendar events."""
        # Generate emails with varied characteristics
        for i in range(self.initial_emails):
            if i == 0:
                # Always include one VIP urgent email
                email = self.state_manager.generate_realistic_email(
                    customer_tier="vip", 
                    base_urgency=8
                )
            elif i == 1:
                # Include one free tier email
                email = self.state_manager.generate_realistic_email(
                    customer_tier="free",
                    base_urgency=random.randint(2, 5)
                )
            else:
                # Random emails
                email = self.state_manager.generate_realistic_email()
            
            self.state_manager.add_email(email)
        
        # Generate tasks with some conflicts
        for i in range(self.initial_tasks):
            conflicting = i == 1  # Make second task have conflicting deadline
            task = self.state_manager.generate_realistic_task(
                conflicting_deadline=conflicting
            )
            self.state_manager.add_task(task)
        
        # Generate calendar events with potential conflicts
        for i in range(self.initial_events):
            conflict = i == (self.initial_events - 1)  # Last event may conflict
            event = self.state_manager.generate_calendar_event(
                potential_conflict=conflict
            )
            self.state_manager.add_calendar_event(event)
    
    def _compute_comprehensive_reward(self, action: Action, base_reward: Reward, multi_agent_action: Optional[MultiAgentAction] = None) -> Reward:
        """
        Compute comprehensive reward using all graders.
        
        Args:
            action: Legacy action taken (converted from multi-agent if applicable)
            base_reward: Base reward from state manager
            multi_agent_action: Original multi-agent action (if applicable)
            
        Returns:
            Enhanced reward with grader evaluations including coordination score
        """
        grader_results = {}
        
        # Email grading (deterministic comparison)
        if action.email_actions:
            # Prepare predicted labels from actions
            predicted_labels = {}
            ground_truth = {}
            
            for email_action in action.email_actions:
                email_id = email_action.get("email_id")
                if email_id in self.state_manager.emails:
                    email = self.state_manager.emails[email_id]
                    
                    # Extract predicted classification from action
                    predicted_labels[email_id] = {
                        "urgency": email.urgency,  # Agent's perceived urgency
                        "customer_tier": email.customer_tier,  # Agent's perceived tier
                        "action": email_action.get("action_type", "reply")
                    }
                    
                    # Get ground truth from state manager
                    if email_id in self.state_manager.ground_truth.correct_email_labels:
                        gt = self.state_manager.ground_truth.correct_email_labels[email_id]
                        ground_truth[email_id] = {
                            "true_urgency": gt.get("true_urgency", email.urgency),
                            "customer_tier": gt.get("customer_tier", email.customer_tier),
                            "ideal_action": gt.get("ideal_action", "reply")
                        }
            
            # Grade email classification accuracy
            if predicted_labels and ground_truth:
                email_result = self.email_grader.grade(predicted_labels, ground_truth)
                grader_results["email"] = email_result
        
        # Response grading (for email responses)
        if action.email_actions:
            response_results = []
            for email_action in action.email_actions:
                email_id = email_action.get("email_id")
                if email_id in self.state_manager.emails and email_action.get("action_type") == "reply":
                    email = self.state_manager.emails[email_id]
                    
                    # Get the actual response content from the action
                    response_text = email_action.get("response_content", "")
                    
                    if response_text:  # Only grade if there's actual response content
                        # Grade response quality using new interface
                        response_result = self.response_grader.grade(
                            response_text=response_text,
                            email_text=email.text,
                            customer_tier=email.customer_tier,
                            urgency=email.urgency
                        )
                        response_results.append(response_result)
            
            if response_results:
                # Average the response scores and combine details
                avg_score = sum(r["score"] for r in response_results) / len(response_results)
                combined_details = {}
                for result in response_results:
                    for key, value in result.get("details", {}).items():
                        if key not in combined_details:
                            combined_details[key] = []
                        combined_details[key].append(value)
                
                grader_results["response"] = {
                    "score": avg_score,
                    "details": combined_details
                }
        
        # Decision grading (for task prioritization and scheduling)
        if action.task_priorities or action.scheduling or action.email_actions:
            # Prepare agent decisions
            agent_decisions = {
                "task_priorities": action.task_priorities,
                "email_actions": [
                    {**email_action, "order": i} 
                    for i, email_action in enumerate(action.email_actions)
                ],
                "ignored_items": action.skip_ids
            }
            
            # Get optimal priorities from ground truth
            optimal_priorities = {
                "task_priorities": self.state_manager.ground_truth.optimal_priorities,
                "vip_emails": [
                    email_id for email_id, email_info in self.state_manager.ground_truth.correct_email_labels.items()
                    if email_info.get("customer_tier") == "vip"
                ],
                "low_value_items": []  # Could be enhanced with specific low-value items
            }
            
            # Prepare ground truth context
            ground_truth_context = {
                "tasks": {
                    task_id: {
                        "importance": task.importance if hasattr(task, 'importance') else 5,
                        "deadline": task.deadline
                    }
                    for task_id, task in self.state_manager.tasks.items()
                },
                "emails": {
                    email_id: {
                        "customer_tier": email.customer_tier,
                        "urgency": email.urgency
                    }
                    for email_id, email in self.state_manager.emails.items()
                }
            }
            
            # Grade decision quality using new interface
            decision_result = self.decision_grader.grade(
                agent_decisions, optimal_priorities, ground_truth_context
            )
            grader_results["decision"] = decision_result
        
        # Scheduling grading (for calendar scheduling)
        if action.scheduling:
            # Prepare scheduled events from action
            scheduled_events = []
            for schedule_item in action.scheduling:
                scheduled_events.append({
                    "id": schedule_item.get("item_id", "unknown"),
                    "start_time": schedule_item.get("scheduled_time", 0),
                    "duration": schedule_item.get("duration", 30),
                    "priority": schedule_item.get("priority", 5),
                    "deadline": schedule_item.get("deadline"),
                    "item_type": schedule_item.get("item_type", "task")
                })
            
            # Get existing calendar events
            existing_events = []
            for event in self.state_manager.calendar_events.values():
                existing_events.append({
                    "id": event.event_id,
                    "start_time": event.time,
                    "duration": event.duration,
                    "priority": 5,  # Default priority for existing events
                    "item_type": "existing_event"
                })
            
            # Prepare context for scheduling grader
            scheduling_context = {
                "total_time_available": self.state_manager.time_remaining,
                "current_time": 480 - self.state_manager.time_remaining,  # Convert to elapsed time
                "existing_events": existing_events,
                "energy_budget": self.state_manager.energy_budget
            }
            
            # Grade scheduling quality
            scheduling_result = self.scheduling_grader.grade(
                scheduled_events, {}, scheduling_context
            )
            grader_results["scheduling"] = scheduling_result
        
        # Coordination grading (for multi-agent actions)
        coordination_grader = CoordinationGrader()
        if multi_agent_action is not None:
            # Multi-agent coordination evaluation
            observation_data = {
                "emails": {email_id: email.model_dump() for email_id, email in self.state_manager.emails.items()},
                "tasks": {task_id: task.model_dump() for task_id, task in self.state_manager.tasks.items()},
                "calendar_events": {event_id: event.model_dump() for event_id, event in self.state_manager.calendar_events.items()},
                "time_remaining": self.state_manager.time_remaining,
                "energy_budget": self.state_manager.energy_budget
            }
            
            coordination_result = coordination_grader.grade_coordination(multi_agent_action, observation_data)
            grader_results["coordination"] = coordination_result
        else:
            # Single-agent mode - perfect coordination by definition
            coordination_result = coordination_grader.grade_coordination(
                MultiAgentAction(email_actions=action.email_actions, task_priorities=action.task_priorities, 
                               scheduling=action.scheduling, skip_ids=action.skip_ids), 
                {}
            )
            grader_results["coordination"] = coordination_result
        
        # Efficiency grading (based on time and energy usage)
        efficiency_score = self._calculate_efficiency_score(action, base_reward)
        grader_results["efficiency"] = {"score": efficiency_score, "details": {}}
        
        # Prepare context for penalty detection
        context = {
            "action_complexity": len(action.email_actions) + len(action.task_priorities) + len(action.scheduling),
            "time_pressure": 1.0 - (self.state_manager.time_remaining / 480),
            "energy_pressure": 1.0 - (self.state_manager.energy_budget / 100),
            "deadlines_missed": self.state_manager.performance_metrics.get("deadlines_missed", 0),
            "vip_emails_count": len([
                email_id for email_id, email in self.state_manager.emails.items()
                if email.customer_tier == "vip"
            ]),
            "vip_emails_handled": len([
                email_action for email_action in action.email_actions
                if email_action.get("email_id") in self.state_manager.emails
                and self.state_manager.emails[email_action["email_id"]].customer_tier == "vip"
            ]),
            "is_multi_agent": multi_agent_action is not None and multi_agent_action.is_multi_agent()
        }
        
        # Use final grader to combine all scores with penalties
        if grader_results:
            final_content = {
                "grader_results": grader_results,
                "context": context
            }
            
            final_reward = self.final_grader.grade(final_content)
            
            # Add coordination score to breakdown
            if hasattr(final_reward, 'breakdown') and isinstance(final_reward.breakdown, dict):
                final_reward.breakdown["coordination_score"] = coordination_result["coordination_score"]
                final_reward.breakdown["coordination_details"] = coordination_result["details"]
            
            # Integrate delayed consequences from base reward
            if hasattr(base_reward, 'breakdown') and isinstance(base_reward.breakdown, dict):
                base_breakdown = base_reward.breakdown
                
                # Add delayed consequences if present in base reward
                if "delayed_consequences" in base_breakdown:
                    delayed_penalty = base_breakdown["delayed_consequences"]
                    
                    # Update final reward score
                    adjusted_score = final_reward.score + delayed_penalty  # delayed_penalty is already negative
                    final_reward.score = max(0.0, min(1.0, adjusted_score))
                    
                    # Add to breakdown
                    if hasattr(final_reward, 'breakdown') and isinstance(final_reward.breakdown, dict):
                        final_reward.breakdown["delayed_consequences"] = delayed_penalty
                        final_reward.breakdown["base_score_before_delayed"] = final_reward.breakdown.get("final_score", final_reward.score)
                        final_reward.breakdown["final_score"] = final_reward.score
            
            return final_reward
        else:
            # No grader results, return base reward with coordination info
            if hasattr(base_reward, 'breakdown') and isinstance(base_reward.breakdown, dict):
                base_reward.breakdown["coordination_score"] = coordination_result["coordination_score"]
                base_reward.breakdown["coordination_details"] = coordination_result["details"]
            
            return base_reward
    
    def _calculate_efficiency_score(self, action: Action, base_reward: Reward) -> float:
        """Calculate efficiency score based on time and energy usage."""
        efficiency_factors = []
        
        # Time efficiency (how much work done vs time spent)
        time_used = 480 - self.state_manager.time_remaining
        if time_used > 0:
            work_done = len(action.email_actions) + len(action.task_priorities) + len(action.scheduling)
            time_efficiency = min(1.0, work_done / (time_used / 60))  # Work per hour
            efficiency_factors.append(time_efficiency)
        
        # Energy efficiency (work done vs energy spent)
        energy_used = 100 - self.state_manager.energy_budget
        if energy_used > 0:
            work_done = len(action.email_actions) + len(action.task_priorities) + len(action.scheduling)
            energy_efficiency = min(1.0, work_done / (energy_used / 10))  # Work per 10 energy units
            efficiency_factors.append(energy_efficiency)
        
        # Action efficiency (quality of actions taken)
        action_efficiency = base_reward.breakdown.get("efficiency_bonus", 0.5)
        efficiency_factors.append(action_efficiency)
        
        # Return average efficiency if we have factors, otherwise neutral score
        if efficiency_factors:
            return sum(efficiency_factors) / len(efficiency_factors)
        else:
            return 0.5  # Neutral efficiency score
    
    def _generate_decision_reasoning(self, action: Action) -> str:
        """Generate reasoning text for decision grading."""
        reasoning_parts = []
        
        if action.email_actions:
            reasoning_parts.append(f"Handling {len(action.email_actions)} emails based on urgency and customer tier")
        
        if action.task_priorities:
            reasoning_parts.append(f"Prioritizing {len(action.task_priorities)} tasks using importance and deadline analysis")
        
        if action.scheduling:
            reasoning_parts.append(f"Scheduling {len(action.scheduling)} items to optimize time utilization")
        
        if action.skip_ids:
            reasoning_parts.append(f"Deferring {len(action.skip_ids)} lower-priority items")
        
        return ". ".join(reasoning_parts) if reasoning_parts else "Taking comprehensive action to manage workload"
    
    def _generate_alternatives(self, action: Action) -> list:
        """Generate alternative approaches for decision grading."""
        alternatives = []
        
        if action.email_actions:
            alternatives.append("Handle all emails immediately regardless of priority")
            alternatives.append("Defer all non-urgent emails to focus on tasks")
        
        if action.task_priorities:
            alternatives.append("Complete tasks in order of arrival (FIFO)")
            alternatives.append("Focus only on highest importance tasks")
        
        if action.scheduling:
            alternatives.append("Schedule all items back-to-back without buffers")
            alternatives.append("Spread items evenly across available time")
        
        return alternatives[:3]  # Limit to 3 alternatives
    
    def _simulate_step_consequences(self) -> None:
        """Simulate consequences and time passage for this step."""
        # Simulate 10-15 minutes of time passage per step
        time_passage = random.randint(10, 15)
        self.state_manager.simulate_time_passage(time_passage)
        
        # Occasionally generate new items (20% chance)
        if random.random() < 0.2:
            new_email = self.state_manager.generate_realistic_email()
            self.state_manager.add_email(new_email)
        
        if random.random() < 0.15:
            new_task = self.state_manager.generate_realistic_task()
            self.state_manager.add_task(new_task)
    
    def _check_episode_done(self) -> bool:
        """Check if episode should end."""
        # Episode ends if:
        # 1. Maximum steps reached
        if self.current_step >= self.max_steps:
            return True
        
        # 2. No time remaining
        if self.state_manager.time_remaining <= 0:
            return True
        
        # 3. Energy completely depleted
        if self.state_manager.energy_budget <= 0:
            return True
        
        # 4. All items completed (rare but possible)
        if (len(self.state_manager.emails) == 0 and 
            len(self.state_manager.tasks) == 0 and
            len(self.state_manager.calendar_events) == 0):
            return True
        
        return False
    
    def _get_step_info(self) -> Dict[str, Any]:
        """Get information dictionary for step return."""
        return {
            "step": self.current_step,
            "max_steps": self.max_steps,
            "time_remaining": self.state_manager.time_remaining,
            "energy_budget": self.state_manager.energy_budget,
            "total_reward": self.total_reward,
            "average_reward": self.total_reward / self.current_step if self.current_step > 0 else 0.0,
            "items_remaining": {
                "emails": len(self.state_manager.emails),
                "tasks": len(self.state_manager.tasks),
                "events": len(self.state_manager.calendar_events)
            },
            "consequences": {
                "pending": len(self.state_manager.pending_consequences),
                "processed": len(self.state_manager.processed_consequences),
                "future_penalties": len(self.state_manager.future_penalties)
            },
            "performance_metrics": self.state_manager.performance_metrics.copy(),
            "episode_done_reason": self._get_done_reason() if self.done else None
        }
    
    def _get_done_reason(self) -> str:
        """Get reason why episode ended."""
        if self.current_step >= self.max_steps:
            return "max_steps_reached"
        elif self.state_manager.time_remaining <= 0:
            return "time_exhausted"
        elif self.state_manager.energy_budget <= 0:
            return "energy_depleted"
        elif (len(self.state_manager.emails) == 0 and 
              len(self.state_manager.tasks) == 0 and
              len(self.state_manager.calendar_events) == 0):
            return "all_items_completed"
        else:
            return "unknown"
    
    def _generate_decision_explanation(self, action: Action, reward: Reward) -> Dict[str, Any]:
        """
        Generate deterministic rule-based explanation for decision outcomes.
        
        Analyzes the action taken and provides insights into:
        - VIP customer handling
        - Priority management efficiency
        - Time and resource utilization
        - Strategic recommendations
        
        Args:
            action: The action that was executed
            reward: The reward received for the action
            
        Returns:
            Dictionary containing explanation of decision outcomes
        """
        explanation = {
            "missed_vip": False,
            "low_priority_handled": False,
            "time_wasted": 0,
            "better_strategy": "current_strategy_optimal"
        }
        
        # Analyze VIP handling
        explanation["missed_vip"] = self._detect_missed_vip_customers(action)
        
        # Analyze priority efficiency
        explanation["low_priority_handled"] = self._detect_low_priority_handling(action)
        
        # Analyze time efficiency
        explanation["time_wasted"] = self._calculate_time_waste(action)
        
        # Generate strategic recommendation
        explanation["better_strategy"] = self._suggest_better_strategy(action, reward, explanation)
        
        # Add detailed analysis
        explanation["detailed_analysis"] = self._generate_detailed_analysis(action, reward, explanation)
        
        # Add performance insights
        explanation["performance_insights"] = self._generate_performance_insights(action, reward)
        
        return explanation
    
    def _detect_missed_vip_customers(self, action: Action) -> bool:
        """
        Detect if VIP customers were ignored or handled inappropriately.
        
        Args:
            action: The action to analyze
            
        Returns:
            True if VIP customers were missed or poorly handled
        """
        # Get all VIP emails in current state
        vip_emails = [
            email_id for email_id, email in self.state_manager.emails.items()
            if email.customer_tier == "vip"
        ]
        
        if not vip_emails:
            return False  # No VIP emails to handle
        
        # Check if VIP emails were handled
        handled_emails = {ea.get("email_id") for ea in action.email_actions}
        skipped_emails = set(action.skip_ids)
        
        # VIP emails that were completely ignored
        ignored_vip = set(vip_emails) - handled_emails
        
        # VIP emails that were explicitly skipped
        skipped_vip = set(vip_emails) & skipped_emails
        
        # VIP emails handled with low priority
        low_priority_vip = []
        for email_action in action.email_actions:
            email_id = email_action.get("email_id")
            if email_id in vip_emails:
                priority = email_action.get("priority", "normal")
                action_type = email_action.get("action_type", "reply")
                
                # VIP should get high priority and immediate action
                if priority != "high" or action_type in ["defer", "archive"]:
                    low_priority_vip.append(email_id)
        
        # Return True if any VIP mishandling detected
        return len(ignored_vip) > 0 or len(skipped_vip) > 0 or len(low_priority_vip) > 0
    
    def _detect_low_priority_handling(self, action: Action) -> bool:
        """
        Detect if low-priority items were handled while high-priority items were ignored.
        
        Args:
            action: The action to analyze
            
        Returns:
            True if inefficient priority handling detected
        """
        # Analyze email priority handling
        handled_low_priority_emails = False
        ignored_high_priority_emails = False
        
        handled_email_ids = {ea.get("email_id") for ea in action.email_actions}
        
        for email_id, email in self.state_manager.emails.items():
            is_handled = email_id in handled_email_ids
            is_high_priority = email.urgency >= 7 or email.customer_tier == "vip"
            is_low_priority = email.urgency <= 3 and email.customer_tier != "vip"
            
            if is_handled and is_low_priority:
                handled_low_priority_emails = True
            elif not is_handled and is_high_priority:
                ignored_high_priority_emails = True
        
        # Analyze task priority handling
        handled_low_priority_tasks = False
        ignored_high_priority_tasks = False
        
        # Get task priorities from action
        task_priority_map = {tp.get("task_id"): tp.get("priority_level", 5) 
                           for tp in action.task_priorities}
        
        # Check if low importance tasks got high priority while high importance tasks got low priority
        for task_id, task in self.state_manager.tasks.items():
            assigned_priority = task_priority_map.get(task_id, 5)
            
            # High importance task (8+) given low priority (1-4)
            if task.importance >= 8 and assigned_priority <= 4:
                ignored_high_priority_tasks = True
            
            # Low importance task (1-3) given high priority (8+)
            elif task.importance <= 3 and assigned_priority >= 8:
                handled_low_priority_tasks = True
        
        return (handled_low_priority_emails and ignored_high_priority_emails) or \
               (handled_low_priority_tasks and ignored_high_priority_tasks)
    
    def _calculate_time_waste(self, action: Action) -> int:
        """
        Calculate estimated time wasted due to inefficient decisions.
        
        Args:
            action: The action to analyze
            
        Returns:
            Estimated time wasted in minutes
        """
        time_waste = 0
        
        # Time wasted on scheduling conflicts
        scheduled_items = action.scheduling
        for i, item1 in enumerate(scheduled_items):
            for item2 in scheduled_items[i+1:]:
                if self._items_have_time_conflict(item1, item2):
                    # Conflict resolution typically wastes 10-15 minutes
                    time_waste += 12
        
        # Time wasted on inappropriate email responses
        for email_action in action.email_actions:
            email_id = email_action.get("email_id")
            if email_id in self.state_manager.emails:
                email = self.state_manager.emails[email_id]
                action_type = email_action.get("action_type", "reply")
                
                # Escalating low-urgency emails wastes time
                if email.urgency <= 4 and action_type == "escalate":
                    time_waste += 8
                
                # Deferring urgent emails wastes time (will need immediate attention later)
                elif email.urgency >= 8 and action_type == "defer":
                    time_waste += 15
        
        # Time wasted on poor task scheduling
        for schedule_item in scheduled_items:
            task_id = schedule_item.get("item_id")
            scheduled_time = schedule_item.get("scheduled_time", 0)
            
            if task_id in self.state_manager.tasks:
                task = self.state_manager.tasks[task_id]
                
                # Scheduling low-importance tasks during prime time (first 2 hours)
                if task.importance <= 4 and scheduled_time <= 120:
                    time_waste += 5
                
                # Scheduling high-importance tasks too late (near deadline)
                elif task.importance >= 8 and (task.deadline - scheduled_time) <= 30:
                    time_waste += 10
        
        # Time wasted on excessive email responses
        response_count = len([ea for ea in action.email_actions if ea.get("action_type") == "reply"])
        if response_count > 5:  # Handling too many emails at once
            time_waste += (response_count - 5) * 3
        
        return time_waste
    
    def _items_have_time_conflict(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if two scheduled items have time conflicts."""
        start1 = item1.get("scheduled_time", 0)
        duration1 = item1.get("duration", 30)
        end1 = start1 + duration1
        
        start2 = item2.get("scheduled_time", 0)
        duration2 = item2.get("duration", 30)
        end2 = start2 + duration2
        
        # Check for overlap
        return start1 < end2 and start2 < end1
    
    def _suggest_better_strategy(self, action: Action, reward: Reward, 
                               explanation: Dict[str, Any]) -> str:
        """
        Suggest a better strategy based on detected issues.
        
        Args:
            action: The action taken
            reward: The reward received
            explanation: Current explanation analysis
            
        Returns:
            String describing a better strategy
        """
        issues = []
        
        if explanation["missed_vip"]:
            issues.append("vip_priority")
        
        if explanation["low_priority_handled"]:
            issues.append("priority_inversion")
        
        if explanation["time_wasted"] > 20:
            issues.append("time_inefficiency")
        
        # Get reward score for strategy assessment
        reward_score = reward.score if hasattr(reward, 'score') else 0.0
        
        # Determine primary issue and suggest strategy
        if not issues:
            if reward_score >= 0.8:
                return "current_strategy_optimal"
            else:
                return "minor_optimizations_possible"
        
        # Prioritize VIP issues
        if "vip_priority" in issues:
            return "vip_first_strategy"
        
        # Address priority inversion
        elif "priority_inversion" in issues:
            return "urgency_based_prioritization"
        
        # Address time inefficiency
        elif "time_inefficiency" in issues:
            return "sequential_scheduling_strategy"
        
        # Multiple issues
        elif len(issues) > 1:
            return "comprehensive_reorganization"
        
        else:
            return "focused_improvement_needed"
    
    def _generate_detailed_analysis(self, action: Action, reward: Reward, 
                                  explanation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed analysis of the decision and its outcomes.
        
        Args:
            action: The action taken
            reward: The reward received
            explanation: Basic explanation dictionary
            
        Returns:
            Detailed analysis dictionary
        """
        analysis = {
            "action_summary": {
                "emails_handled": len(action.email_actions),
                "tasks_prioritized": len(action.task_priorities),
                "items_scheduled": len(action.scheduling),
                "items_skipped": len(action.skip_ids)
            },
            "efficiency_metrics": {},
            "risk_factors": [],
            "strengths": [],
            "weaknesses": []
        }
        
        # Calculate efficiency metrics
        total_items = (len(self.state_manager.emails) + 
                      len(self.state_manager.tasks) + 
                      len(self.state_manager.calendar_events))
        
        items_addressed = (len(action.email_actions) + 
                          len(action.task_priorities) + 
                          len(action.scheduling))
        
        analysis["efficiency_metrics"] = {
            "coverage_ratio": items_addressed / max(total_items, 1),
            "action_density": items_addressed / max(self.current_step, 1),
            "time_utilization": min(1.0, items_addressed * 15 / max(480 - self.state_manager.time_remaining, 1))
        }
        
        # Identify risk factors
        if explanation["missed_vip"]:
            analysis["risk_factors"].append("vip_customer_dissatisfaction")
        
        if explanation["time_wasted"] > 15:
            analysis["risk_factors"].append("deadline_pressure_increase")
        
        if len(action.skip_ids) > 3:
            analysis["risk_factors"].append("backlog_accumulation")
        
        # Identify strengths
        if not explanation["missed_vip"]:
            analysis["strengths"].append("proper_vip_handling")
        
        if explanation["time_wasted"] < 10:
            analysis["strengths"].append("efficient_time_management")
        
        if len(action.scheduling) > 0:
            analysis["strengths"].append("proactive_scheduling")
        
        # Identify weaknesses
        if explanation["low_priority_handled"]:
            analysis["weaknesses"].append("priority_management")
        
        if len(action.email_actions) == 0:
            analysis["weaknesses"].append("customer_communication")
        
        if len(action.task_priorities) == 0:
            analysis["weaknesses"].append("task_organization")
        
        return analysis
    
    def _generate_performance_insights(self, action: Action, reward: Reward) -> Dict[str, Any]:
        """
        Generate performance insights based on reward breakdown.
        
        Args:
            action: The action taken
            reward: The reward received
            
        Returns:
            Performance insights dictionary
        """
        insights = {
            "overall_performance": "unknown",
            "grader_performance": {},
            "improvement_areas": [],
            "next_steps": []
        }
        
        # Overall performance assessment
        reward_score = reward.score if hasattr(reward, 'score') else 0.0
        
        if reward_score >= 0.8:
            insights["overall_performance"] = "excellent"
        elif reward_score >= 0.6:
            insights["overall_performance"] = "good"
        elif reward_score >= 0.4:
            insights["overall_performance"] = "fair"
        else:
            insights["overall_performance"] = "needs_improvement"
        
        # Analyze grader performance if available
        if hasattr(reward, 'breakdown') and isinstance(reward.breakdown, dict):
            grader_scores = reward.breakdown.get("grader_scores", {})
            
            for grader_name, score in grader_scores.items():
                if score < 0.5:
                    insights["grader_performance"][grader_name] = "weak"
                    insights["improvement_areas"].append(grader_name)
                elif score < 0.7:
                    insights["grader_performance"][grader_name] = "moderate"
                else:
                    insights["grader_performance"][grader_name] = "strong"
        
        # Generate next steps based on performance
        if "email" in insights["improvement_areas"]:
            insights["next_steps"].append("Focus on accurate email classification and appropriate actions")
        
        if "response" in insights["improvement_areas"]:
            insights["next_steps"].append("Improve response quality and completeness")
        
        if "decision" in insights["improvement_areas"]:
            insights["next_steps"].append("Enhance task prioritization and VIP handling")
        
        if "scheduling" in insights["improvement_areas"]:
            insights["next_steps"].append("Optimize scheduling to avoid conflicts and meet deadlines")
        
        if not insights["next_steps"]:
            insights["next_steps"].append("Maintain current performance level and look for minor optimizations")
        
        return insights

    def render(self, mode: str = "human") -> Optional[str]:
        """
        Render the environment state.
        
        Args:
            mode: Rendering mode ("human" or "ansi")
            
        Returns:
            String representation if mode is "ansi"
        """
        output = []
        output.append(f"=== OpsPilot Environment (Episode {self.episode_count}, Step {self.current_step}/{self.max_steps}) ===")
        output.append(f"Time Remaining: {self.state_manager.time_remaining}min | Energy: {self.state_manager.energy_budget}/100")
        output.append(f"Total Reward: {self.total_reward:.3f} | Done: {self.done}")
        output.append("")
        
        # Show current items
        output.append(f"📧 Emails ({len(self.state_manager.emails)}):")
        for email in list(self.state_manager.emails.values())[:3]:  # Show first 3
            output.append(f"  {email.id}: {email.customer_tier} | urgency {email.urgency}")
        
        output.append(f"📋 Tasks ({len(self.state_manager.tasks)}):")
        for task in list(self.state_manager.tasks.values())[:3]:  # Show first 3
            output.append(f"  {task.task_id}: importance {task.importance} | deadline {task.deadline}min")
        
        output.append(f"📅 Events ({len(self.state_manager.calendar_events)}):")
        for event in list(self.state_manager.calendar_events.values())[:2]:  # Show first 2
            output.append(f"  {event.event_id}: {event.time}min | duration {event.duration}min")
        
        # Show consequences
        if self.state_manager.pending_consequences:
            output.append(f"⚠️  Pending Consequences ({len(self.state_manager.pending_consequences)}):")
            for consequence in self.state_manager.pending_consequences[:2]:
                output.append(f"  {consequence.event_type.value}: {consequence.description}")
        
        output.append("=" * 60)
        
        rendered = "\n".join(output)
        
        if mode == "human":
            print(rendered)
        elif mode == "ansi":
            return rendered
        
        return None

    def simulate_counterfactual(self, action: Action) -> Dict[str, Any]:
        """
        Simulate alternative action outcomes without modifying real state.
        
        This method enables counterfactual evaluation by:
        1. Safely cloning the current environment state
        2. Running the provided action on the cloned state
        3. Computing rewards using existing graders
        4. Generating optimal and random baseline actions
        5. Comparing performance across all scenarios
        
        Args:
            action: The action to evaluate counterfactually
            
        Returns:
            Dictionary containing:
            - actual_score: Score for the provided action
            - optimal_score: Score for the optimal action
            - random_score: Score for a random baseline action
            - regret: optimal_score - actual_score
            - action_analysis: Detailed breakdown of each action's performance
        """
        if self.done:
            raise RuntimeError("Cannot simulate counterfactuals on completed episode. Call reset() first.")
        
        # Store original state for restoration
        original_state = self._clone_environment_state()
        
        try:
            # 1. Evaluate the provided action
            actual_result = self._simulate_action_on_clone(action, "actual")
            
            # 2. Generate and evaluate optimal action
            optimal_action = self._generate_optimal_action()
            optimal_result = self._simulate_action_on_clone(optimal_action, "optimal")
            
            # 3. Generate and evaluate random baseline action
            random_action = self._generate_random_action()
            random_result = self._simulate_action_on_clone(random_action, "random")
            
            # 4. Calculate regret and comparative metrics
            regret = optimal_result["score"] - actual_result["score"]
            
            # 5. Prepare comprehensive analysis
            counterfactual_analysis = {
                "actual_score": actual_result["score"],
                "optimal_score": optimal_result["score"],
                "random_score": random_result["score"],
                "regret": regret,
                "relative_performance": {
                    "vs_optimal": actual_result["score"] / optimal_result["score"] if optimal_result["score"] > 0 else 1.0,
                    "vs_random": actual_result["score"] / random_result["score"] if random_result["score"] > 0 else 1.0,
                    "improvement_potential": regret / optimal_result["score"] if optimal_result["score"] > 0 else 0.0
                },
                "action_analysis": {
                    "actual": {
                        "action": action.model_dump(),
                        "result": actual_result,
                        "strategy": "provided_action"
                    },
                    "optimal": {
                        "action": optimal_action.model_dump(),
                        "result": optimal_result,
                        "strategy": "ground_truth_heuristics"
                    },
                    "random": {
                        "action": random_action.model_dump(),
                        "result": random_result,
                        "strategy": "random_baseline"
                    }
                },
                "insights": self._generate_counterfactual_insights(
                    actual_result, optimal_result, random_result, action, optimal_action
                ),
                "environment_context": {
                    "step": self.current_step,
                    "time_remaining": self.state_manager.time_remaining,
                    "energy_budget": self.state_manager.energy_budget,
                    "items_count": {
                        "emails": len(self.state_manager.emails),
                        "tasks": len(self.state_manager.tasks),
                        "events": len(self.state_manager.calendar_events)
                    }
                }
            }
            
            return counterfactual_analysis
            
        finally:
            # Always restore original state to ensure no mutation
            self._restore_environment_state(original_state)
    
    def _clone_environment_state(self) -> Dict[str, Any]:
        """
        Create a deep copy of the current environment state.
        
        Returns:
            Dictionary containing all state information needed for restoration
        """
        return {
            # Environment-level state
            "current_step": self.current_step,
            "total_reward": self.total_reward,
            "done": self.done,
            "episode_actions": copy.deepcopy(self.episode_actions),
            "episode_rewards": copy.deepcopy(self.episode_rewards),
            
            # State manager state (deep copy to avoid mutation)
            "state_manager": {
                "current_time": self.state_manager.current_time,
                "time_remaining": self.state_manager.time_remaining,
                "energy_budget": self.state_manager.energy_budget,
                "emails": copy.deepcopy({eid: email.model_dump() for eid, email in self.state_manager.emails.items()}),
                "tasks": copy.deepcopy({tid: task.model_dump() for tid, task in self.state_manager.tasks.items()}),
                "calendar_events": copy.deepcopy({eid: event.model_dump() for eid, event in self.state_manager.calendar_events.items()}),
                "ground_truth": copy.deepcopy({
                    "correct_email_labels": self.state_manager.ground_truth.correct_email_labels,
                    "ideal_responses": self.state_manager.ground_truth.ideal_responses,
                    "optimal_priorities": self.state_manager.ground_truth.optimal_priorities,
                    "task_dependencies": self.state_manager.ground_truth.task_dependencies,
                    "valid_schedules": self.state_manager.ground_truth.valid_schedules,
                    "expected_completion_times": self.state_manager.ground_truth.expected_completion_times,
                    "energy_costs": self.state_manager.ground_truth.energy_costs
                }),
                "pending_consequences": copy.deepcopy([c.__dict__ for c in self.state_manager.pending_consequences]),
                "processed_consequences": copy.deepcopy([c.__dict__ for c in self.state_manager.processed_consequences]),
                "performance_metrics": copy.deepcopy(self.state_manager.performance_metrics),
                "random_seed": self.state_manager.random_seed
            },
            
            # Random state for reproducibility
            "random_state": random.getstate()
        }
    
    def _restore_environment_state(self, state: Dict[str, Any]) -> None:
        """
        Restore environment to a previously cloned state.
        
        Args:
            state: State dictionary from _clone_environment_state()
        """
        # Restore environment-level state
        self.current_step = state["current_step"]
        self.total_reward = state["total_reward"]
        self.done = state["done"]
        self.episode_actions = copy.deepcopy(state["episode_actions"])
        self.episode_rewards = copy.deepcopy(state["episode_rewards"])
        
        # Restore state manager state
        sm_state = state["state_manager"]
        self.state_manager.current_time = sm_state["current_time"]
        self.state_manager.time_remaining = sm_state["time_remaining"]
        self.state_manager.energy_budget = sm_state["energy_budget"]
        
        # Restore collections (need to recreate objects from dicts)
        from models import Email, Task, CalendarEvent
        
        self.state_manager.emails = {
            eid: Email(**email_data) for eid, email_data in sm_state["emails"].items()
        }
        self.state_manager.tasks = {
            tid: Task(**task_data) for tid, task_data in sm_state["tasks"].items()
        }
        self.state_manager.calendar_events = {
            eid: CalendarEvent(**event_data) for eid, event_data in sm_state["calendar_events"].items()
        }
        
        # Restore ground truth
        gt_data = sm_state["ground_truth"]
        self.state_manager.ground_truth.correct_email_labels = copy.deepcopy(gt_data["correct_email_labels"])
        self.state_manager.ground_truth.ideal_responses = copy.deepcopy(gt_data["ideal_responses"])
        self.state_manager.ground_truth.optimal_priorities = copy.deepcopy(gt_data["optimal_priorities"])
        self.state_manager.ground_truth.task_dependencies = copy.deepcopy(gt_data["task_dependencies"])
        self.state_manager.ground_truth.valid_schedules = copy.deepcopy(gt_data["valid_schedules"])
        self.state_manager.ground_truth.expected_completion_times = copy.deepcopy(gt_data["expected_completion_times"])
        self.state_manager.ground_truth.energy_costs = copy.deepcopy(gt_data["energy_costs"])
        
        # Restore consequences (recreate ConsequenceEvent objects)
        from env.state import ConsequenceEvent, ConsequenceType
        
        self.state_manager.pending_consequences = []
        for cons_data in sm_state["pending_consequences"]:
            consequence = ConsequenceEvent(
                event_type=ConsequenceType(cons_data["event_type"]),
                trigger_time=cons_data["trigger_time"],
                severity=cons_data.get("severity", 0.5),
                description=cons_data["description"],
                affected_items=cons_data.get("affected_items", []),
                penalty_score=cons_data.get("penalty_score", 0.0)
            )
            self.state_manager.pending_consequences.append(consequence)
        
        self.state_manager.processed_consequences = []
        for cons_data in sm_state["processed_consequences"]:
            consequence = ConsequenceEvent(
                event_type=ConsequenceType(cons_data["event_type"]),
                trigger_time=cons_data["trigger_time"],
                severity=cons_data.get("severity", 0.5),
                description=cons_data["description"],
                affected_items=cons_data.get("affected_items", []),
                penalty_score=cons_data.get("penalty_score", 0.0)
            )
            self.state_manager.processed_consequences.append(consequence)
        
        # Restore performance metrics and random seed
        self.state_manager.performance_metrics = copy.deepcopy(sm_state["performance_metrics"])
        self.state_manager.random_seed = sm_state["random_seed"]
        
        # Restore random state
        random.setstate(state["random_state"])
    
    def _simulate_action_on_clone(self, action: Action, action_type: str) -> Dict[str, Any]:
        """
        Simulate an action on the current (cloned) state and return results.
        
        Args:
            action: Action to simulate
            action_type: Type of action for logging ("actual", "optimal", "random")
            
        Returns:
            Dictionary with simulation results including score and breakdown
        """
        try:
            # Apply action and get base reward
            base_reward = self.state_manager.process_action(action)
            
            # Compute comprehensive reward using graders
            comprehensive_reward = self._compute_comprehensive_reward(action, base_reward)
            
            # Simulate consequences (but don't advance time significantly for counterfactual)
            original_time = self.state_manager.time_remaining
            original_energy = self.state_manager.energy_budget
            
            # Light simulation - just check immediate consequences
            self.state_manager.simulate_time_passage(5)  # Minimal time passage
            
            return {
                "score": comprehensive_reward.score,
                "breakdown": comprehensive_reward.breakdown,
                "reward_object": comprehensive_reward.model_dump(),
                "action_type": action_type,
                "resource_usage": {
                    "time_used": original_time - self.state_manager.time_remaining,
                    "energy_used": original_energy - self.state_manager.energy_budget
                },
                "items_processed": {
                    "emails": len(action.email_actions),
                    "tasks": len(action.task_priorities),
                    "scheduled": len(action.scheduling),
                    "skipped": len(action.skip_ids)
                }
            }
            
        except Exception as e:
            # Return error result if simulation fails
            return {
                "score": 0.0,
                "breakdown": {"error": str(e)},
                "reward_object": {"score": 0.0, "breakdown": {"error": str(e)}},
                "action_type": action_type,
                "resource_usage": {"time_used": 0, "energy_used": 0},
                "items_processed": {"emails": 0, "tasks": 0, "scheduled": 0, "skipped": 0},
                "simulation_error": str(e)
            }
    
    def _generate_optimal_action(self) -> Action:
        """
        Generate optimal action based on ground truth heuristics.
        
        Uses ground truth information to make the best possible decisions:
        - Prioritize VIP customers first
        - Handle urgent items by true urgency
        - Use optimal task priorities from ground truth
        - Schedule efficiently to avoid conflicts
        
        Returns:
            Optimal action based on ground truth
        """
        email_actions = []
        task_priorities = []
        scheduling = []
        skip_ids = []
        
        # Email actions: Use ground truth for optimal handling
        emails_by_priority = []
        for email_id, email in self.state_manager.emails.items():
            gt_labels = self.state_manager.ground_truth.correct_email_labels.get(email_id, {})
            true_urgency = gt_labels.get("true_urgency", email.urgency)
            
            # Priority score: VIP gets +10, urgency is weighted
            priority_score = true_urgency
            if email.customer_tier == "vip":
                priority_score += 10
            
            emails_by_priority.append((priority_score, email_id, email))
        
        # Sort by priority (highest first)
        emails_by_priority.sort(key=lambda x: x[0], reverse=True)
        
        # Generate optimal email actions
        for priority_score, email_id, email in emails_by_priority[:5]:  # Handle top 5
            gt_labels = self.state_manager.ground_truth.correct_email_labels.get(email_id, {})
            ideal_action = gt_labels.get("ideal_action", "reply")
            
            # Generate ideal response if replying
            response_content = ""
            if ideal_action == "reply":
                ideal_responses = self.state_manager.ground_truth.ideal_responses.get(email_id, {})
                if isinstance(ideal_responses, dict):
                    response_content = ideal_responses.get("content", f"Thank you for contacting us. I will address your {email.customer_tier} priority request immediately.")
                else:
                    # If ideal_responses is a string, use it directly
                    response_content = str(ideal_responses) if ideal_responses else f"Thank you for contacting us. I will address your {email.customer_tier} priority request immediately."
            
            email_actions.append({
                "email_id": email_id,
                "action_type": ideal_action,
                "response_content": response_content,
                "priority": "high" if email.customer_tier == "vip" or email.urgency >= 7 else "normal",
                "estimated_time": 10 if email.customer_tier == "vip" else 15
            })
        
        # Task priorities: Use ground truth optimal priorities
        optimal_task_priorities = self.state_manager.ground_truth.optimal_priorities
        for task_id, task in self.state_manager.tasks.items():
            optimal_priority = optimal_task_priorities.get(task_id, task.importance)
            task_priorities.append({
                "task_id": task_id,
                "priority_level": optimal_priority
            })
        
        # Scheduling: Use ground truth valid schedules
        valid_schedules = self.state_manager.ground_truth.valid_schedules
        current_time = 480 - self.state_manager.time_remaining
        
        # Sort tasks by optimal priority for scheduling
        tasks_for_scheduling = sorted(
            [(optimal_task_priorities.get(tid, task.importance), tid, task) 
             for tid, task in self.state_manager.tasks.items()],
            key=lambda x: x[0], reverse=True
        )
        
        schedule_time = current_time + 15  # Start 15 minutes from now
        for priority, task_id, task in tasks_for_scheduling[:3]:  # Schedule top 3 tasks
            # Check if we have a valid schedule for this task
            if task_id in valid_schedules:
                optimal_time = valid_schedules[task_id].get("optimal_start_time", schedule_time)
                duration = valid_schedules[task_id].get("duration", getattr(task, 'estimated_duration', 60))
            else:
                optimal_time = schedule_time
                duration = getattr(task, 'estimated_duration', 60)  # Default 60 minutes
            
            # Ensure we don't schedule beyond available time
            if optimal_time + duration <= 480:
                scheduling.append({
                    "item_id": task_id,
                    "scheduled_time": optimal_time,
                    "duration": duration,
                    "priority": priority,
                    "deadline": task.deadline,
                    "item_type": "task"
                })
                schedule_time = optimal_time + duration + 10  # 10 min buffer
        
        # Skip low-priority items if time/energy is limited
        if self.state_manager.time_remaining < 120 or self.state_manager.energy_budget < 30:
            for email_id, email in self.state_manager.emails.items():
                if email.urgency <= 3 and email.customer_tier != "vip":
                    if email_id not in [ea["email_id"] for ea in email_actions]:
                        skip_ids.append(email_id)
        
        return Action(
            email_actions=email_actions,
            task_priorities=task_priorities,
            scheduling=scheduling,
            skip_ids=skip_ids
        )
    
    def _generate_random_action(self) -> Action:
        """
        Generate random baseline action for comparison.
        
        Creates a random but valid action to serve as a baseline:
        - Randomly select emails to handle
        - Random task priorities
        - Random scheduling
        - Random items to skip
        
        Returns:
            Random action for baseline comparison
        """
        email_actions = []
        task_priorities = []
        scheduling = []
        skip_ids = []
        
        # Random email actions
        email_list = list(self.state_manager.emails.items())
        random.shuffle(email_list)
        
        for email_id, email in email_list[:random.randint(1, min(4, len(email_list)))]:
            action_types = ["reply", "forward", "escalate", "defer"]
            action_type = random.choice(action_types)
            
            response_content = ""
            if action_type == "reply":
                responses = [
                    "Thank you for your message. I will look into this.",
                    "I have received your request and will respond soon.",
                    "Thank you for contacting us. I will address this matter.",
                    "I appreciate your message and will handle this appropriately."
                ]
                response_content = random.choice(responses)
            
            email_actions.append({
                "email_id": email_id,
                "action_type": action_type,
                "response_content": response_content,
                "priority": random.choice(["high", "normal", "low"]),
                "estimated_time": random.randint(5, 20)
            })
        
        # Random task priorities
        for task_id, task in self.state_manager.tasks.items():
            task_priorities.append({
                "task_id": task_id,
                "priority_level": random.randint(1, 10)
            })
        
        # Random scheduling
        task_list = list(self.state_manager.tasks.items())
        random.shuffle(task_list)
        
        current_time = 480 - self.state_manager.time_remaining
        schedule_time = current_time + random.randint(10, 30)
        
        for task_id, task in task_list[:random.randint(1, min(3, len(task_list)))]:
            duration = getattr(task, 'estimated_duration', 60)  # Default 60 minutes
            if schedule_time + duration <= 480:
                scheduling.append({
                    "item_id": task_id,
                    "scheduled_time": schedule_time,
                    "duration": duration + random.randint(-10, 10),
                    "priority": random.randint(1, 10),
                    "deadline": task.deadline,
                    "item_type": "task"
                })
                schedule_time += duration + random.randint(5, 15)
        
        # Random items to skip
        all_items = list(self.state_manager.emails.keys()) + list(self.state_manager.tasks.keys())
        if all_items and random.random() < 0.3:  # 30% chance to skip some items
            skip_count = random.randint(1, min(2, len(all_items)))
            skip_ids = random.sample(all_items, skip_count)
        
        return Action(
            email_actions=email_actions,
            task_priorities=task_priorities,
            scheduling=scheduling,
            skip_ids=skip_ids
        )
    
    def _generate_counterfactual_insights(self, actual_result: Dict[str, Any], 
                                        optimal_result: Dict[str, Any], 
                                        random_result: Dict[str, Any],
                                        actual_action: Action,
                                        optimal_action: Action) -> Dict[str, Any]:
        """
        Generate insights from counterfactual analysis.
        
        Args:
            actual_result: Results from the actual action
            optimal_result: Results from the optimal action
            random_result: Results from the random action
            actual_action: The actual action taken
            optimal_action: The optimal action generated
            
        Returns:
            Dictionary containing actionable insights
        """
        insights = {
            "performance_assessment": "",
            "key_differences": [],
            "improvement_suggestions": [],
            "strategic_analysis": {},
            "risk_assessment": {}
        }
        
        # Performance assessment
        actual_score = actual_result["score"]
        optimal_score = optimal_result["score"]
        random_score = random_result["score"]
        
        if actual_score >= optimal_score * 0.9:
            insights["performance_assessment"] = "Excellent: Action is near-optimal"
        elif actual_score >= optimal_score * 0.7:
            insights["performance_assessment"] = "Good: Action is reasonably effective"
        elif actual_score >= random_score:
            insights["performance_assessment"] = "Fair: Action beats random baseline but has room for improvement"
        else:
            insights["performance_assessment"] = "Poor: Action performs worse than random baseline"
        
        # Key differences analysis
        actual_breakdown = actual_result.get("breakdown", {})
        optimal_breakdown = optimal_result.get("breakdown", {})
        
        grader_scores = actual_breakdown.get("grader_scores", {})
        optimal_grader_scores = optimal_breakdown.get("grader_scores", {})
        
        for grader_type in ["email", "response", "decision", "scheduling"]:
            actual_grader_score = grader_scores.get(grader_type, 0)
            optimal_grader_score = optimal_grader_scores.get(grader_type, 0)
            
            if optimal_grader_score > 0:
                performance_ratio = actual_grader_score / optimal_grader_score
                if performance_ratio < 0.8:
                    insights["key_differences"].append(
                        f"{grader_type.title()} grader: {performance_ratio:.1%} of optimal performance"
                    )
        
        # Improvement suggestions
        if len(actual_action.email_actions) < len(optimal_action.email_actions):
            insights["improvement_suggestions"].append("Consider handling more high-priority emails")
        
        if actual_breakdown.get("penalties", {}).get("ignoring_vip", 0) > 0:
            insights["improvement_suggestions"].append("Prioritize VIP customers to avoid penalties")
        
        if actual_breakdown.get("penalties", {}).get("conflicts", 0) > 0:
            insights["improvement_suggestions"].append("Improve scheduling to avoid conflicts")
        
        # Strategic analysis
        insights["strategic_analysis"] = {
            "email_strategy": "optimal" if len(actual_action.email_actions) >= len(optimal_action.email_actions) * 0.8 else "suboptimal",
            "task_prioritization": "effective" if actual_breakdown.get("grader_scores", {}).get("decision", 0) > 0.7 else "needs_improvement",
            "time_management": "efficient" if actual_result.get("resource_usage", {}).get("time_used", 0) <= 15 else "inefficient",
            "risk_level": "low" if len(actual_breakdown.get("penalties", {})) <= 1 else "high"
        }
        
        # Risk assessment
        penalties = actual_breakdown.get("penalties", {})
        insights["risk_assessment"] = {
            "penalty_risk": len(penalties),
            "vip_risk": "high" if penalties.get("ignoring_vip", 0) > 0 else "low",
            "scheduling_risk": "high" if penalties.get("conflicts", 0) > 0 else "low",
            "quality_risk": "high" if penalties.get("hallucination", 0) > 0 else "low"
        }
        
        return insights


# Global environment instance
env = Environment()