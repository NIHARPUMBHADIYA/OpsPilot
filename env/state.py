"""State management system for OpsPilot."""

import random
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from models import Email, Task, CalendarEvent, Observation, Action, Reward


class EmailTone(Enum):
    """Email tone types for realistic generation."""
    PROFESSIONAL = "professional"
    URGENT = "urgent"
    ANGRY = "angry"
    CONFUSED = "confused"
    GRATEFUL = "grateful"
    # Adversarial cases
    SARCASTIC = "sarcastic"
    MISLEADING = "misleading"
    INCOMPLETE = "incomplete"
    MIXED_INTENT = "mixed_intent"


class ConsequenceType(Enum):
    """Types of consequences for actions."""
    IGNORED_EMAIL = "ignored_email"
    SCHEDULING_CONFLICT = "scheduling_conflict"
    MISSED_DEADLINE = "missed_deadline"
    ENERGY_DEPLETION = "energy_depletion"


@dataclass
class GroundTruth:
    """Ground truth data for validation and scoring."""
    
    # Email ground truth
    correct_email_labels: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    ideal_responses: Dict[str, str] = field(default_factory=dict)
    
    # Task ground truth
    optimal_priorities: Dict[str, int] = field(default_factory=dict)
    task_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    # Scheduling ground truth
    valid_schedules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    optimal_time_slots: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    
    # Performance metrics
    expected_completion_times: Dict[str, int] = field(default_factory=dict)
    energy_costs: Dict[str, int] = field(default_factory=dict)

@dataclass
class ConsequenceEvent:
    """Represents a consequence of an action or inaction."""
    
    event_type: ConsequenceType
    trigger_time: int  # When the consequence occurs (minutes from start)
    severity: float  # 0.0 to 1.0
    description: str
    affected_items: List[str]  # IDs of affected emails/tasks/events
    penalty_score: float = 0.0


class StateManager:
    """Comprehensive state management system for OpsPilot."""
    
    def __init__(self, random_seed: Optional[int] = None):
        """Initialize state manager with deterministic behavior."""
        self.random_seed = random_seed or 42
        random.seed(self.random_seed)
        
        # Core state
        self.current_time = 0  # Minutes from start
        self.time_remaining = 480  # 8 hours default
        self.energy_budget = 100
        self.session_start = datetime.now()
        self.current_step = 0  # Track current step for delayed consequences
        
        # Ground truth storage
        self.ground_truth = GroundTruth()
        
        # Active items
        self.emails: Dict[str, Email] = {}
        self.tasks: Dict[str, Task] = {}
        self.calendar_events: Dict[str, CalendarEvent] = {}
        
        # Tracking and consequences
        self.action_history: List[Dict[str, Any]] = []
        self.pending_consequences: List[ConsequenceEvent] = []
        self.processed_consequences: List[ConsequenceEvent] = []
        
        # Delayed consequences system
        self.future_penalties: List[Dict[str, Any]] = []
        
        # Data generation templates
        self._init_data_templates()
        
        # Performance tracking
        self.performance_metrics = {
            "emails_processed": 0,
            "tasks_completed": 0,
            "conflicts_created": 0,
            "deadlines_missed": 0,
            "customer_satisfaction": 1.0,
            "efficiency_score": 1.0,
            "delayed_penalties_applied": 0,
            "total_delayed_penalty": 0.0
        }
    
    def _init_data_templates(self) -> None:
        """Initialize templates for realistic data generation."""
        self.email_templates = {
            EmailTone.PROFESSIONAL: [
                "Dear {name}, I hope this email finds you well. I am writing to {purpose}.",
                "Hello {name}, I wanted to reach out regarding {purpose}.",
                "Good {time_of_day} {name}, I am contacting you about {purpose}."
            ],
            EmailTone.URGENT: [
                "URGENT: {name}, we need immediate attention on {purpose}!",
                "{name} - This is time-sensitive! {purpose} requires immediate action.",
                "PRIORITY: {name}, please address {purpose} as soon as possible."
            ],
            EmailTone.ANGRY: [
                "{name}, I am extremely frustrated with {purpose}. This is unacceptable!",
                "This is ridiculous! {name}, {purpose} has been ignored for too long!",
                "{name} - I demand immediate action on {purpose}. This is the last time I'm asking!"
            ],
            EmailTone.CONFUSED: [
                "Hi {name}, I'm not sure I understand {purpose}. Can you help clarify?",
                "{name}, I'm having trouble with {purpose}. Could you provide guidance?",
                "Hello {name}, I'm confused about {purpose}. What should I do next?"
            ],
            EmailTone.GRATEFUL: [
                "Thank you so much {name}! Your help with {purpose} was amazing.",
                "{name}, I really appreciate your assistance with {purpose}.",
                "Dear {name}, I wanted to express my gratitude for {purpose}."
            ],
            # Adversarial cases that challenge classification and response
            EmailTone.SARCASTIC: [
                "Great service... NOT. {name}, I guess {purpose} is just too hard for you?",
                "Oh wonderful {name}, another issue with {purpose}. I'm SO surprised.",
                "Thanks for nothing {name}. {purpose} is still broken. What a shock."
            ],
            EmailTone.MISLEADING: [
                "Hi {name}, everything is fine with {purpose}... just kidding, it's completely broken!",
                "No rush {name}, but {purpose} is only costing us thousands per hour. Take your time.",
                "Just a quick note {name} - {purpose} might need a tiny bit of attention. Like, immediately."
            ],
            EmailTone.INCOMPLETE: [
                "Hey {name}, so about {purpose}... anyway, can you just",
                "{name} - {purpose} is... well, you know. Please fix",
                "Hi {name}, I guess I'll just leave this here about {purpose}..."
            ],
            EmailTone.MIXED_INTENT: [
                "Dear {name}, I love your service! But {purpose} is terrible and I want a refund immediately.",
                "Hi {name}, great job on everything except {purpose} which is the worst thing ever created.",
                "Thank you {name} for your help, though {purpose} makes me want to cancel everything."
            ]
        }
        
        self.email_purposes = [
            "account access issues",
            "billing discrepancies", 
            "service outages",
            "feature requests",
            "technical support",
            "subscription changes",
            "data export requests",
            "password reset problems",
            "integration questions",
            "performance concerns"
        ]
        
        self.customer_names = [
            "John Smith", "Sarah Johnson", "Mike Chen", "Lisa Rodriguez",
            "David Kim", "Emma Wilson", "Alex Thompson", "Maria Garcia",
            "James Brown", "Jennifer Lee", "Robert Taylor", "Amanda Davis"
        ]
        
        self.task_descriptions = [
            "Review customer feedback and prepare response strategy",
            "Update system documentation for new features",
            "Investigate reported performance issues",
            "Prepare monthly analytics report",
            "Conduct security audit of user accounts",
            "Optimize database query performance",
            "Test new feature deployment",
            "Review and approve pending user requests",
            "Update customer onboarding process",
            "Analyze support ticket trends"
        ]
        
        # Noise patterns for realistic data
        self.typo_patterns = {
            'a': ['@', 'q', 's'],
            'e': ['3', 'w', 'r'],
            'i': ['1', 'u', 'o'],
            'o': ['0', 'p', 'i'],
            'u': ['y', 'i', 'o'],
            's': ['z', 'a', 'd'],
            't': ['r', 'y', 'g'],
            'n': ['b', 'm', 'h']
        }
    def generate_realistic_email(self, customer_tier: str = None, 
                               base_urgency: int = None) -> Email:
        """Generate a realistic email with noise, typos, and varied tone."""
        # Determine customer tier
        if customer_tier is None:
            customer_tier = random.choices(
                ["free", "premium", "vip"],
                weights=[0.6, 0.3, 0.1]  # Most customers are free tier
            )[0]
        
        # Determine tone based on customer tier and random factors
        # Include adversarial cases with controlled probability
        base_tones = [EmailTone.PROFESSIONAL, EmailTone.URGENT, EmailTone.ANGRY, 
                     EmailTone.CONFUSED, EmailTone.GRATEFUL]
        adversarial_tones = [EmailTone.SARCASTIC, EmailTone.MISLEADING, 
                           EmailTone.INCOMPLETE, EmailTone.MIXED_INTENT]
        
        # 20% chance of adversarial tone (seed-controlled)
        if random.random() < 0.2:
            tone = random.choice(adversarial_tones)
        else:
            tone_weights = {
                "free": [0.4, 0.2, 0.3, 0.1, 0.0],  # More angry/confused
                "premium": [0.6, 0.2, 0.1, 0.05, 0.05],  # More professional
                "vip": [0.8, 0.1, 0.05, 0.025, 0.025]  # Mostly professional
            }
            
            tone = random.choices(
                base_tones,
                weights=tone_weights[customer_tier]
            )[0]
        
        # Generate base urgency if not provided
        if base_urgency is None:
            urgency_ranges = {
                "free": (1, 6),
                "premium": (3, 8),
                "vip": (5, 10)
            }
            base_urgency = random.randint(*urgency_ranges[customer_tier])
        
        # Adjust urgency based on tone
        tone_urgency_modifiers = {
            EmailTone.PROFESSIONAL: 0,
            EmailTone.URGENT: +3,
            EmailTone.ANGRY: +2,
            EmailTone.CONFUSED: -1,
            EmailTone.GRATEFUL: -2,
            # Adversarial tones - often mask true urgency
            EmailTone.SARCASTIC: +1,  # Usually indicates frustration
            EmailTone.MISLEADING: +2,  # Often hides urgent issues
            EmailTone.INCOMPLETE: 0,   # Unclear urgency
            EmailTone.MIXED_INTENT: +1  # Conflicting signals
        }
        
        final_urgency = max(1, min(10, base_urgency + tone_urgency_modifiers[tone]))
        
        # Generate email content
        name = random.choice(self.customer_names)
        purpose = random.choice(self.email_purposes)
        time_of_day = random.choice(["morning", "afternoon", "evening"])
        
        template = random.choice(self.email_templates[tone])
        email_text = template.format(
            name=name,
            purpose=purpose,
            time_of_day=time_of_day
        )
        
        # Add noise and typos for realism
        if random.random() < 0.3:  # 30% chance of typos
            email_text = self._add_typos(email_text)
        
        if tone == EmailTone.ANGRY and random.random() < 0.5:
            email_text = email_text.upper()  # Angry emails often in caps
        
        # Generate timestamp (deterministic based on seed)
        # Use a fixed base time and add deterministic offset
        base_time = datetime(2026, 3, 27, 17, 0, 0)  # Fixed base time
        timestamp_offset = random.randint(-120, 0)  # Up to 2 hours ago
        timestamp = (base_time + timedelta(minutes=timestamp_offset)).isoformat() + "Z"
        
        # Create email
        email_id = f"email_{len(self.emails) + 1:03d}"
        email = Email(
            id=email_id,
            text=email_text,
            customer_tier=customer_tier,
            urgency=final_urgency,
            timestamp=timestamp
        )
        
        # Store ground truth with adversarial case handling
        true_intent = self._determine_true_intent(tone, final_urgency, customer_tier)
        
        self.ground_truth.correct_email_labels[email_id] = {
            "true_urgency": final_urgency,
            "customer_tier": customer_tier,
            "tone": tone.value,
            "apparent_tone": tone.value,  # What the text appears to convey
            "true_intent": true_intent,   # What the customer actually needs
            "is_adversarial": tone in [EmailTone.SARCASTIC, EmailTone.MISLEADING, 
                                     EmailTone.INCOMPLETE, EmailTone.MIXED_INTENT],
            "requires_immediate_response": final_urgency >= 8,
            "escalation_needed": customer_tier == "vip" and final_urgency >= 7,
            "estimated_response_time": self._calculate_response_time(customer_tier, final_urgency)
        }
        
        # Generate ideal response
        self.ground_truth.ideal_responses[email_id] = self._generate_ideal_response(
            customer_tier, tone, purpose, final_urgency
        )
        
        return email
    
    def _determine_true_intent(self, tone: EmailTone, urgency: int, customer_tier: str) -> str:
        """Determine the true intent behind adversarial emails."""
        if tone == EmailTone.SARCASTIC:
            # Sarcastic emails usually indicate frustration with real issues
            return "frustrated_customer_needs_help"
        elif tone == EmailTone.MISLEADING:
            # Misleading emails often downplay urgent issues
            return "urgent_issue_disguised_as_minor"
        elif tone == EmailTone.INCOMPLETE:
            # Incomplete emails may hide important context
            return "unclear_request_needs_clarification"
        elif tone == EmailTone.MIXED_INTENT:
            # Mixed intent emails have conflicting messages
            return "conflicted_customer_needs_resolution"
        else:
            # Non-adversarial tones have straightforward intent
            intent_map = {
                EmailTone.PROFESSIONAL: "standard_business_request",
                EmailTone.URGENT: "time_sensitive_issue",
                EmailTone.ANGRY: "escalated_complaint",
                EmailTone.CONFUSED: "needs_guidance",
                EmailTone.GRATEFUL: "positive_feedback"
            }
            return intent_map.get(tone, "standard_request")
    
    def _add_typos(self, text: str) -> str:
        """Add realistic typos to text."""
        words = text.split()
        modified_words = []
        
        for word in words:
            if len(word) > 3 and random.random() < 0.2:  # 20% chance per word
                # Choose random position to modify
                pos = random.randint(1, len(word) - 2)
                char = word[pos].lower()
                
                if char in self.typo_patterns:
                    replacement = random.choice(self.typo_patterns[char])
                    word = word[:pos] + replacement + word[pos+1:]
            
            modified_words.append(word)
        
        return " ".join(modified_words)
    
    def _calculate_response_time(self, customer_tier: str, urgency: int) -> int:
        """Calculate ideal response time in minutes."""
        base_times = {
            "free": 240,      # 4 hours
            "premium": 120,   # 2 hours  
            "vip": 30         # 30 minutes
        }
        
        urgency_multiplier = max(0.1, (11 - urgency) / 10)
        return int(base_times[customer_tier] * urgency_multiplier)
    
    def _generate_ideal_response(self, customer_tier: str, tone: EmailTone, 
                               purpose: str, urgency: int) -> str:
        """Generate ideal response for the email, handling adversarial cases."""
        # Handle adversarial cases by responding to true intent, not apparent tone
        if tone == EmailTone.SARCASTIC:
            # Acknowledge frustration without matching sarcasm
            return f"I understand your frustration with {purpose}. Let me personally address this issue and ensure it's resolved properly."
        elif tone == EmailTone.MISLEADING:
            # Recognize the hidden urgency and respond appropriately
            return f"Thank you for bringing {purpose} to our attention. I can see this needs immediate action - I'm escalating this right away."
        elif tone == EmailTone.INCOMPLETE:
            # Proactively seek clarification while offering help
            return f"I'd like to help you with {purpose}. Could you provide a bit more detail so I can give you the best solution?"
        elif tone == EmailTone.MIXED_INTENT:
            # Address both positive and negative aspects diplomatically
            return f"Thank you for your feedback. I'm glad some aspects are working well, and I'll personally ensure we resolve the issues with {purpose}."
        elif tone == EmailTone.ANGRY:
            return f"I sincerely apologize for the inconvenience with {purpose}. Let me personally ensure this is resolved immediately."
        elif tone == EmailTone.URGENT:
            return f"Thank you for bringing {purpose} to our attention. I'm prioritizing this and will have an update within the hour."
        elif tone == EmailTone.CONFUSED:
            return f"I'd be happy to help clarify {purpose}. Let me walk you through the process step by step."
        elif tone == EmailTone.GRATEFUL:
            return f"You're very welcome! I'm glad I could help with {purpose}. Please don't hesitate to reach out if you need anything else."
        else:
            return f"Thank you for contacting us about {purpose}. I'll review this and get back to you with a solution."
    def generate_realistic_task(self, base_importance: int = None,
                              conflicting_deadline: bool = False) -> Task:
        """Generate a realistic task with potential deadline conflicts."""
        # Generate task details
        task_id = f"task_{len(self.tasks) + 1:03d}"
        description = random.choice(self.task_descriptions)
        
        # Add complexity variations to description
        complexity_modifiers = [
            "urgent", "complex", "high-priority", "critical", "routine",
            "follow-up", "preliminary", "comprehensive", "detailed"
        ]
        
        if random.random() < 0.4:  # 40% chance of modifier
            modifier = random.choice(complexity_modifiers)
            description = f"{modifier.title()} {description.lower()}"
        
        # Determine importance
        if base_importance is None:
            base_importance = random.randint(1, 10)
        
        # Generate deadline with potential conflicts
        if conflicting_deadline:
            # Create intentionally tight deadline
            deadline = random.randint(15, 60)  # 15 minutes to 1 hour
        else:
            # Normal deadline distribution
            deadline_ranges = [
                (30, 120),    # 30min - 2hrs (urgent)
                (120, 480),   # 2hrs - 8hrs (normal)
                (480, 1440),  # 8hrs - 24hrs (long-term)
            ]
            weights = [0.3, 0.5, 0.2]  # Most tasks are normal timeframe
            deadline_range = random.choices(deadline_ranges, weights=weights)[0]
            deadline = random.randint(*deadline_range)
        
        # Create task
        task = Task(
            task_id=task_id,
            description=description,
            deadline=deadline,
            importance=base_importance
        )
        
        # Store ground truth
        optimal_priority = self._calculate_optimal_priority(base_importance, deadline)
        self.ground_truth.optimal_priorities[task_id] = optimal_priority
        
        # Calculate expected completion time
        complexity_score = len(description.split()) / 10  # Rough complexity measure
        base_time = 30 + (base_importance * 5) + (complexity_score * 10)
        expected_time = int(base_time * random.uniform(0.8, 1.2))  # Add variance
        
        self.ground_truth.expected_completion_times[task_id] = expected_time
        self.ground_truth.energy_costs[task_id] = max(5, base_importance + random.randint(-2, 3))
        
        # Generate dependencies occasionally
        if len(self.tasks) > 0 and random.random() < 0.2:  # 20% chance
            existing_task_ids = list(self.tasks.keys())
            dependency = random.choice(existing_task_ids)
            self.ground_truth.task_dependencies[task_id] = [dependency]
        
        return task
    
    def _calculate_optimal_priority(self, importance: int, deadline: int) -> int:
        """Calculate optimal priority based on importance and deadline."""
        # Eisenhower Matrix inspired calculation
        urgency_score = max(1, 11 - (deadline // 60))  # Convert to urgency (1-10)
        
        # Weight importance and urgency
        priority_score = (importance * 0.6) + (urgency_score * 0.4)
        return max(1, min(10, int(priority_score)))
    
    def generate_calendar_event(self, potential_conflict: bool = False) -> CalendarEvent:
        """Generate a calendar event with potential scheduling conflicts."""
        event_id = f"event_{len(self.calendar_events) + 1:03d}"
        
        if potential_conflict and len(self.calendar_events) > 0:
            # Create overlapping event
            existing_event = random.choice(list(self.calendar_events.values()))
            # Overlap with existing event
            time_start = existing_event.time + random.randint(-15, 15)
            duration = random.randint(30, 120)
        else:
            # Normal scheduling
            time_start = random.randint(30, 400)  # 30min to ~7hrs from now
            duration = random.choice([15, 30, 45, 60, 90, 120])  # Common meeting lengths
        
        event = CalendarEvent(
            event_id=event_id,
            time=max(0, time_start),
            duration=duration
        )
        
        # Store optimal scheduling info
        self.ground_truth.valid_schedules[event_id] = {
            "optimal_start": time_start,
            "buffer_needed": 15,  # 15 minutes buffer
            "can_reschedule": random.random() < 0.7,  # 70% can be rescheduled
            "priority": random.randint(1, 10)
        }
        
        return event
    
    def add_email(self, email: Email) -> None:
        """Add email to state and schedule consequences."""
        self.emails[email.id] = email
        
        # Schedule consequence for ignored emails
        if email.urgency >= 7:  # High urgency emails
            consequence_time = self.current_time + random.randint(60, 180)  # 1-3 hours
            consequence = ConsequenceEvent(
                event_type=ConsequenceType.IGNORED_EMAIL,
                trigger_time=consequence_time,
                severity=min(1.0, email.urgency / 10),
                description=f"Email {email.id} from {email.customer_tier} customer escalated due to no response",
                affected_items=[email.id],
                penalty_score=email.urgency * 0.1
            )
            self.pending_consequences.append(consequence)
    
    def add_task(self, task: Task) -> None:
        """Add task to state and schedule deadline consequences."""
        self.tasks[task.task_id] = task
        
        # Schedule deadline consequence
        deadline_time = self.current_time + task.deadline
        consequence = ConsequenceEvent(
            event_type=ConsequenceType.MISSED_DEADLINE,
            trigger_time=deadline_time,
            severity=task.importance / 10,
            description=f"Task {task.task_id} deadline missed",
            affected_items=[task.task_id],
            penalty_score=task.importance * 0.15
        )
        self.pending_consequences.append(consequence)
    
    def add_calendar_event(self, event: CalendarEvent) -> None:
        """Add calendar event and check for conflicts."""
        self.calendar_events[event.event_id] = event
        
        # Check for scheduling conflicts
        conflicts = self._detect_scheduling_conflicts(event)
        if conflicts:
            consequence = ConsequenceEvent(
                event_type=ConsequenceType.SCHEDULING_CONFLICT,
                trigger_time=event.time,
                severity=len(conflicts) * 0.3,
                description=f"Event {event.event_id} conflicts with {len(conflicts)} other events",
                affected_items=[event.event_id] + conflicts,
                penalty_score=len(conflicts) * 0.2
            )
            self.pending_consequences.append(consequence)
    def _detect_scheduling_conflicts(self, new_event: CalendarEvent) -> List[str]:
        """Detect scheduling conflicts with existing events."""
        conflicts = []
        new_start = new_event.time
        new_end = new_event.time + new_event.duration
        
        for event_id, event in self.calendar_events.items():
            if event_id == new_event.event_id:
                continue
                
            event_start = event.time
            event_end = event.time + event.duration
            
            # Check for overlap
            if (new_start < event_end and new_end > event_start):
                conflicts.append(event_id)
        
        return conflicts
    
    def process_action(self, action: Action) -> Reward:
        """Process an action and return reward with consequences."""
        action_time = datetime.now()
        
        # Process any delayed consequences from previous actions first
        delayed_penalty = self.process_delayed_consequences(self.current_step)
        
        # Analyze current action and schedule future delayed consequences
        self.detect_and_schedule_delayed_consequences(action)
        
        # Calculate base reward
        reward_breakdown = {}
        total_score = 0.0
        
        # Process email actions
        if action.email_actions:
            email_score = self._score_email_actions(action.email_actions)
            reward_breakdown["email_handling"] = email_score
            total_score += email_score * 0.3
            
            # Update energy and time
            energy_cost = len(action.email_actions) * 5
            time_cost = len(action.email_actions) * 10
            self._consume_resources(energy_cost, time_cost)
        
        # Process task priorities
        if action.task_priorities:
            task_score = self._score_task_priorities(action.task_priorities)
            reward_breakdown["task_prioritization"] = task_score
            total_score += task_score * 0.3
        
        # Process scheduling
        if action.scheduling:
            schedule_score = self._score_scheduling(action.scheduling)
            reward_breakdown["time_management"] = schedule_score
            total_score += schedule_score * 0.2
        
        # Process skipped items
        if action.skip_ids:
            skip_penalty = self._calculate_skip_penalty(action.skip_ids)
            reward_breakdown["skip_penalty"] = skip_penalty
            total_score += skip_penalty  # This will be negative
        
        # Apply immediate consequences
        consequence_penalty = self._process_pending_consequences()
        if consequence_penalty < 0:
            reward_breakdown["consequences"] = consequence_penalty
            total_score += consequence_penalty
        
        # Apply delayed consequences from previous actions
        if delayed_penalty > 0:
            reward_breakdown["delayed_consequences"] = -delayed_penalty  # Negative because it's a penalty
            total_score -= delayed_penalty
        
        # Efficiency bonus
        efficiency_bonus = self._calculate_efficiency_bonus()
        if efficiency_bonus > 0:
            reward_breakdown["efficiency_bonus"] = efficiency_bonus
            total_score += efficiency_bonus
        
        # Normalize score
        final_score = max(0.0, min(1.0, total_score))
        
        # Record action with delayed consequences info
        action_record = {
            "timestamp": action_time.isoformat(),
            "step": self.current_step,
            "action": action.model_dump(),
            "score": final_score,
            "breakdown": reward_breakdown,
            "delayed_penalty_applied": delayed_penalty,
            "future_penalties_scheduled": len([p for p in self.future_penalties if p["created_at_step"] == self.current_step])
        }
        
        self.action_history.append(action_record)
        
        return Reward(score=final_score, breakdown=reward_breakdown)
    
    def _score_email_actions(self, email_actions: List[Dict[str, Any]]) -> float:
        """Score email handling actions."""
        if not email_actions:
            return 0.0
        
        total_score = 0.0
        for action in email_actions:
            email_id = action.get("email_id")
            action_type = action.get("action_type")
            
            if email_id not in self.emails:
                continue
            
            email = self.emails[email_id]
            ground_truth = self.ground_truth.correct_email_labels.get(email_id, {})
            
            # Score based on urgency and customer tier
            base_score = 0.5
            
            # Urgency handling
            if email.urgency >= 8 and action_type in ["reply", "escalate"]:
                base_score += 0.3
            elif email.urgency <= 3 and action_type == "defer":
                base_score += 0.2
            
            # Customer tier handling
            if email.customer_tier == "vip" and action_type in ["reply", "escalate"]:
                base_score += 0.2
            elif email.customer_tier == "free" and action_type == "archive":
                base_score += 0.1
            
            # Response time bonus
            if ground_truth.get("requires_immediate_response") and action_type == "reply":
                base_score += 0.2
            
            total_score += base_score
            
            # Remove consequence if handled
            self._remove_email_consequences(email_id)
        
        return min(1.0, total_score / len(email_actions))
    
    def _score_task_priorities(self, task_priorities: List[Dict[str, Any]]) -> float:
        """Score task prioritization decisions."""
        if not task_priorities:
            return 0.0
        
        total_score = 0.0
        for priority in task_priorities:
            task_id = priority.get("task_id")
            assigned_priority = priority.get("priority_level")
            
            if task_id not in self.tasks:
                continue
            
            optimal_priority = self.ground_truth.optimal_priorities.get(task_id, 5)
            
            # Score based on how close to optimal
            priority_diff = abs(assigned_priority - optimal_priority)
            priority_score = max(0.0, 1.0 - (priority_diff / 10))
            
            # Bonus for handling dependencies
            if task_id in self.ground_truth.task_dependencies:
                dependencies = self.ground_truth.task_dependencies[task_id]
                # Check if dependencies are handled first
                for dep_id in dependencies:
                    dep_priority = next((p["priority_level"] for p in task_priorities 
                                       if p["task_id"] == dep_id), None)
                    if dep_priority and dep_priority > assigned_priority:
                        priority_score += 0.1
            
            total_score += priority_score
        
        return min(1.0, total_score / len(task_priorities))
    
    def _score_scheduling(self, scheduling: List[Dict[str, Any]]) -> float:
        """Score scheduling decisions."""
        if not scheduling:
            return 0.0
        
        total_score = 0.0
        scheduled_times = []
        
        for schedule in scheduling:
            item_id = schedule.get("item_id")
            scheduled_time = schedule.get("scheduled_time")
            duration = schedule.get("duration", 30)
            
            scheduled_times.append((scheduled_time, scheduled_time + duration))
            
            # Base score for scheduling
            base_score = 0.5
            
            # Check for optimal timing
            if item_id in self.ground_truth.valid_schedules:
                optimal_info = self.ground_truth.valid_schedules[item_id]
                optimal_start = optimal_info["optimal_start"]
                
                # Score based on proximity to optimal time
                time_diff = abs(scheduled_time - optimal_start)
                if time_diff <= 30:  # Within 30 minutes
                    base_score += 0.3
                elif time_diff <= 60:  # Within 1 hour
                    base_score += 0.1
            
            total_score += base_score
        
        # Penalty for overlapping schedules
        overlap_penalty = self._calculate_overlap_penalty(scheduled_times)
        total_score -= overlap_penalty
        
        return max(0.0, min(1.0, total_score / len(scheduling)))
    
    def _calculate_overlap_penalty(self, scheduled_times: List[Tuple[int, int]]) -> float:
        """Calculate penalty for overlapping scheduled times."""
        penalty = 0.0
        for i, (start1, end1) in enumerate(scheduled_times):
            for j, (start2, end2) in enumerate(scheduled_times[i+1:], i+1):
                if start1 < end2 and end1 > start2:  # Overlap detected
                    overlap_duration = min(end1, end2) - max(start1, start2)
                    penalty += overlap_duration / 60  # Penalty per hour of overlap
        
        return penalty
    
    def _calculate_skip_penalty(self, skip_ids: List[str]) -> float:
        """Calculate penalty for skipping items."""
        penalty = 0.0
        
        for item_id in skip_ids:
            if item_id in self.emails:
                email = self.emails[item_id]
                # Higher penalty for skipping urgent/VIP emails
                penalty -= (email.urgency / 10) * 0.1
                if email.customer_tier == "vip":
                    penalty -= 0.05
            elif item_id in self.tasks:
                task = self.tasks[item_id]
                # Penalty based on importance and deadline proximity
                penalty -= (task.importance / 10) * 0.1
                if task.deadline <= 60:  # Less than 1 hour
                    penalty -= 0.05
        
        return penalty
    def _process_pending_consequences(self) -> float:
        """Process consequences that have triggered."""
        penalty = 0.0
        triggered_consequences = []
        
        for consequence in self.pending_consequences:
            if self.current_time >= consequence.trigger_time:
                penalty -= consequence.penalty_score
                triggered_consequences.append(consequence)
                
                # Apply specific consequence effects
                if consequence.event_type == ConsequenceType.IGNORED_EMAIL:
                    self._escalate_ignored_email(consequence.affected_items[0])
                elif consequence.event_type == ConsequenceType.MISSED_DEADLINE:
                    self._handle_missed_deadline(consequence.affected_items[0])
                elif consequence.event_type == ConsequenceType.SCHEDULING_CONFLICT:
                    self._handle_scheduling_conflict(consequence.affected_items)
        
        # Move triggered consequences to processed
        for consequence in triggered_consequences:
            self.pending_consequences.remove(consequence)
            self.processed_consequences.append(consequence)
        
        return penalty
    
    def _escalate_ignored_email(self, email_id: str) -> None:
        """Handle escalation of ignored email."""
        if email_id in self.emails:
            email = self.emails[email_id]
            # Increase urgency
            original_urgency = email.urgency
            email.urgency = min(10, email.urgency + 2)
            
            # Update performance metrics
            self.performance_metrics["customer_satisfaction"] *= 0.9
            
            # Create follow-up email if customer is VIP
            if email.customer_tier == "vip":
                follow_up = self.generate_realistic_email(
                    customer_tier="vip",
                    base_urgency=10
                )
                follow_up.text = f"ESCALATION: Previous email {email_id} was ignored. " + follow_up.text
                self.add_email(follow_up)
    
    def _handle_missed_deadline(self, task_id: str) -> None:
        """Handle missed task deadline."""
        if task_id in self.tasks:
            self.performance_metrics["deadlines_missed"] += 1
            self.performance_metrics["efficiency_score"] *= 0.95
            
            # Create follow-up task if important
            task = self.tasks[task_id]
            if task.importance >= 7:
                follow_up = self.generate_realistic_task(
                    base_importance=min(10, task.importance + 1),
                    conflicting_deadline=True
                )
                follow_up.description = f"URGENT: Complete overdue task - {task.description}"
                self.add_task(follow_up)
    
    def _handle_scheduling_conflict(self, affected_items: List[str]) -> None:
        """Handle scheduling conflicts."""
        self.performance_metrics["conflicts_created"] += 1
        
        # Randomly reschedule one of the conflicting events
        if len(affected_items) > 1:
            event_to_reschedule = random.choice(affected_items[1:])  # Don't reschedule the first
            if event_to_reschedule in self.calendar_events:
                event = self.calendar_events[event_to_reschedule]
                # Move to a later time
                event.time += random.randint(60, 180)  # 1-3 hours later
    
    def _remove_email_consequences(self, email_id: str) -> None:
        """Remove pending consequences for handled email."""
        self.pending_consequences = [
            c for c in self.pending_consequences 
            if not (c.event_type == ConsequenceType.IGNORED_EMAIL and email_id in c.affected_items)
        ]
    
    def _calculate_efficiency_bonus(self) -> float:
        """Calculate efficiency bonus based on resource usage."""
        bonus = 0.0
        
        # Energy efficiency bonus
        if self.energy_budget > 70:
            bonus += 0.05
        elif self.energy_budget > 50:
            bonus += 0.02
        
        # Time efficiency bonus
        time_used_ratio = (480 - self.time_remaining) / 480
        if time_used_ratio < 0.8:  # Finished early
            bonus += 0.03
        
        return bonus
    
    def _consume_resources(self, energy_cost: int, time_cost: int) -> None:
        """Consume energy and time resources."""
        self.energy_budget = max(0, self.energy_budget - energy_cost)
        self.time_remaining = max(0, self.time_remaining - time_cost)
        self.current_time += time_cost
        
        # Energy depletion consequence
        if self.energy_budget <= 20:
            consequence = ConsequenceEvent(
                event_type=ConsequenceType.ENERGY_DEPLETION,
                trigger_time=self.current_time,
                severity=0.8,
                description="Low energy affecting performance",
                affected_items=[],
                penalty_score=0.1
            )
            self.pending_consequences.append(consequence)
    
    def get_current_observation(self, include_history: bool = True,
                              max_history_items: int = 50) -> Observation:
        """Get current state as an observation."""
        history = []
        if include_history:
            for action in self.action_history[-max_history_items:]:
                # Handle both old and new action record formats
                if isinstance(action, dict):
                    if "timestamp" in action and "score" in action:
                        # New format with delayed consequences
                        timestamp = action["timestamp"]
                        score = action["score"]
                        delayed_penalty = action.get("delayed_penalty_applied", 0)
                        
                        if delayed_penalty > 0:
                            history.append(f"{timestamp}: Score {score:.2f} (delayed penalty: -{delayed_penalty:.2f})")
                        else:
                            history.append(f"{timestamp}: Score {score:.2f}")
                    elif "type" in action and action["type"] == "delayed_penalty_applied":
                        # Delayed penalty application record
                        step = action.get("step", "?")
                        penalty = action.get("penalty", 0)
                        reason = action.get("reason", "Unknown")
                        history.append(f"Step {step}: Penalty -{penalty:.2f} - {reason}")
        
        return Observation(
            emails=list(self.emails.values()),
            tasks=list(self.tasks.values()),
            calendar=list(self.calendar_events.values()),
            time_remaining=self.time_remaining,
            energy_budget=self.energy_budget,
            history=history
        )
    
    def simulate_time_passage(self, minutes: int) -> None:
        """Simulate passage of time and trigger consequences."""
        self.current_time += minutes
        self.time_remaining = max(0, self.time_remaining - minutes)
        
        # Process any triggered consequences
        self._process_pending_consequences()
        
        # Randomly generate new items
        if random.random() < 0.3:  # 30% chance of new email
            new_email = self.generate_realistic_email()
            self.add_email(new_email)
        
        if random.random() < 0.2:  # 20% chance of new task
            new_task = self.generate_realistic_task()
            self.add_task(new_task)
    
    def reset_state(self) -> None:
        """Reset the state manager to initial conditions."""
        random.seed(self.random_seed)
        
        self.current_time = 0
        self.time_remaining = 480
        self.energy_budget = 100
        self.current_step = 0  # Reset step counter
        self.session_start = datetime.now()
        
        self.emails.clear()
        self.tasks.clear()
        self.calendar_events.clear()
        
        self.action_history.clear()
        self.pending_consequences.clear()
        self.processed_consequences.clear()
        self.future_penalties.clear()  # Clear delayed consequences
        
        self.ground_truth = GroundTruth()
        
        self.performance_metrics = {
            "emails_processed": 0,
            "tasks_completed": 0,
            "conflicts_created": 0,
            "deadlines_missed": 0,
            "customer_satisfaction": 1.0,
            "efficiency_score": 1.0,
            "delayed_penalties_applied": 0,
            "total_delayed_penalty": 0.0
        }
    
    def add_delayed_penalty(self, trigger_step: int, penalty: float, reason: str, 
                          affected_items: List[str] = None) -> None:
        """
        Add a delayed penalty that will be applied in a future step.
        
        Args:
            trigger_step: Step number when penalty should be applied
            penalty: Penalty amount (positive value, will be subtracted from reward)
            reason: Human-readable reason for the penalty
            affected_items: Optional list of item IDs that caused this penalty
        """
        delayed_penalty = {
            "trigger_step": trigger_step,
            "penalty": penalty,
            "reason": reason,
            "affected_items": affected_items or [],
            "created_at_step": self.current_step,
            "timestamp": datetime.now().isoformat()
        }
        
        self.future_penalties.append(delayed_penalty)
    
    def process_delayed_consequences(self, current_step: int) -> float:
        """
        Process any delayed penalties that should trigger at the current step.
        
        Args:
            current_step: Current step number
            
        Returns:
            Total penalty amount applied this step
        """
        self.current_step = current_step  # Update current step
        total_penalty = 0.0
        penalties_to_remove = []
        
        for i, penalty_info in enumerate(self.future_penalties):
            if penalty_info["trigger_step"] <= current_step:
                # Apply the penalty
                penalty_amount = penalty_info["penalty"]
                total_penalty += penalty_amount
                
                # Update performance metrics
                self.performance_metrics["delayed_penalties_applied"] += 1
                self.performance_metrics["total_delayed_penalty"] += penalty_amount
                
                # Log the penalty application
                self.action_history.append({
                    "type": "delayed_penalty_applied",
                    "step": current_step,
                    "penalty": penalty_amount,
                    "reason": penalty_info["reason"],
                    "affected_items": penalty_info["affected_items"],
                    "delay_steps": current_step - penalty_info["created_at_step"]
                })
                
                # Mark for removal
                penalties_to_remove.append(i)
        
        # Remove processed penalties (in reverse order to maintain indices)
        for i in reversed(penalties_to_remove):
            self.future_penalties.pop(i)
        
        return total_penalty
    
    def detect_and_schedule_delayed_consequences(self, action: Action) -> None:
        """
        Analyze the current action and schedule appropriate delayed consequences.
        
        Args:
            action: The action being processed
        """
        # Detect ignored emails and schedule future penalties
        self._schedule_ignored_email_penalties(action)
        
        # Detect scheduling conflicts and schedule future penalties
        self._schedule_scheduling_conflict_penalties(action)
        
        # Detect missed VIP handling and schedule future penalties
        self._schedule_vip_neglect_penalties(action)
        
        # Detect task deadline issues and schedule future penalties
        self._schedule_deadline_pressure_penalties(action)
    
    def _schedule_ignored_email_penalties(self, action: Action) -> None:
        """Schedule penalties for ignored emails based on their urgency and customer tier."""
        handled_email_ids = {ea.get("email_id") for ea in action.email_actions}
        skipped_email_ids = set(action.skip_ids)
        
        for email_id, email in self.emails.items():
            # Check if email was completely ignored (not handled and not explicitly skipped)
            if email_id not in handled_email_ids and email_id not in skipped_email_ids:
                # Calculate penalty based on urgency and customer tier
                base_penalty = 0.05  # Base penalty for ignoring any email
                
                # Urgency multiplier
                urgency_multiplier = email.urgency / 10.0
                
                # Customer tier multiplier
                tier_multiplier = {
                    "vip": 3.0,
                    "premium": 2.0,
                    "free": 1.0
                }.get(email.customer_tier, 1.0)
                
                penalty = base_penalty * urgency_multiplier * tier_multiplier
                
                # Schedule penalty 2-4 steps in the future (escalation time)
                delay_steps = 2 if email.customer_tier == "vip" else 3 if email.urgency >= 7 else 4
                trigger_step = self.current_step + delay_steps
                
                reason = f"Ignored {email.customer_tier} email (urgency {email.urgency}) - customer escalation"
                
                self.add_delayed_penalty(
                    trigger_step=trigger_step,
                    penalty=penalty,
                    reason=reason,
                    affected_items=[email_id]
                )
    
    def _schedule_scheduling_conflict_penalties(self, action: Action) -> None:
        """Schedule penalties for scheduling conflicts."""
        scheduled_items = action.scheduling
        
        # Check for conflicts between scheduled items
        for i, item1 in enumerate(scheduled_items):
            for item2 in scheduled_items[i+1:]:
                if self._items_have_time_conflict(item1, item2):
                    # Calculate penalty based on conflict severity
                    overlap_duration = self._calculate_conflict_overlap(item1, item2)
                    base_penalty = 0.08  # Base conflict penalty
                    
                    # Severity based on overlap duration
                    severity_multiplier = min(2.0, overlap_duration / 30.0)  # Max 2x for 30+ min overlap
                    
                    penalty = base_penalty * severity_multiplier
                    
                    # Conflicts cause immediate disruption (1-2 steps delay)
                    trigger_step = self.current_step + random.randint(1, 2)
                    
                    reason = f"Scheduling conflict between {item1.get('item_id', 'unknown')} and {item2.get('item_id', 'unknown')} - productivity loss"
                    
                    self.add_delayed_penalty(
                        trigger_step=trigger_step,
                        penalty=penalty,
                        reason=reason,
                        affected_items=[item1.get('item_id', ''), item2.get('item_id', '')]
                    )
    
    def _schedule_vip_neglect_penalties(self, action: Action) -> None:
        """Schedule penalties for poor VIP customer handling."""
        handled_emails = {ea.get("email_id"): ea for ea in action.email_actions}
        
        for email_id, email in self.emails.items():
            if email.customer_tier == "vip":
                email_action = handled_emails.get(email_id)
                
                # Check for poor VIP handling
                poor_handling = False
                penalty_reason = ""
                
                if not email_action:
                    # VIP email completely ignored
                    poor_handling = True
                    penalty_reason = "VIP customer email completely ignored"
                elif email_action.get("priority", "normal") != "high":
                    # VIP email not given high priority
                    poor_handling = True
                    penalty_reason = "VIP customer not given high priority treatment"
                elif email_action.get("action_type") in ["defer", "archive"]:
                    # VIP email deferred or archived
                    poor_handling = True
                    penalty_reason = f"VIP customer email {email_action.get('action_type')}d inappropriately"
                
                if poor_handling:
                    # VIP neglect has serious consequences
                    penalty = 0.15  # Significant penalty for VIP issues
                    
                    # VIP complaints escalate quickly (1-3 steps)
                    trigger_step = self.current_step + random.randint(1, 3)
                    
                    full_reason = f"{penalty_reason} - VIP customer complaint escalation"
                    
                    self.add_delayed_penalty(
                        trigger_step=trigger_step,
                        penalty=penalty,
                        reason=full_reason,
                        affected_items=[email_id]
                    )
    
    def _schedule_deadline_pressure_penalties(self, action: Action) -> None:
        """Schedule penalties for poor deadline management."""
        task_priorities = {tp.get("task_id"): tp.get("priority_level", 5) for tp in action.task_priorities}
        scheduled_tasks = {s.get("item_id"): s for s in action.scheduling if s.get("item_type") == "task"}
        
        for task_id, task in self.tasks.items():
            # Check if high-importance task near deadline is being ignored
            if task.importance >= 8 and task.deadline <= 120:  # High importance, deadline within 2 hours
                task_priority = task_priorities.get(task_id, 0)
                is_scheduled = task_id in scheduled_tasks
                
                if task_priority < 7 and not is_scheduled:
                    # High-importance task near deadline not properly prioritized
                    penalty = 0.12  # Significant penalty for deadline risk
                    
                    # Deadline pressure builds up (2-5 steps)
                    delay_steps = max(2, min(5, task.deadline // 30))  # Scale with deadline
                    trigger_step = self.current_step + delay_steps
                    
                    reason = f"High-importance task '{task_id}' near deadline not prioritized - deadline pressure"
                    
                    self.add_delayed_penalty(
                        trigger_step=trigger_step,
                        penalty=penalty,
                        reason=reason,
                        affected_items=[task_id]
                    )
    
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
    
    def _calculate_conflict_overlap(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> int:
        """Calculate the overlap duration between two conflicting items in minutes."""
        start1 = item1.get("scheduled_time", 0)
        duration1 = item1.get("duration", 30)
        end1 = start1 + duration1
        
        start2 = item2.get("scheduled_time", 0)
        duration2 = item2.get("duration", 30)
        end2 = start2 + duration2
        
        # Calculate overlap
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        return max(0, overlap_end - overlap_start)
    
    def get_delayed_consequences_summary(self) -> Dict[str, Any]:
        """Get summary of current delayed consequences."""
        return {
            "pending_penalties": len(self.future_penalties),
            "total_pending_penalty": sum(p["penalty"] for p in self.future_penalties),
            "next_penalty_step": min((p["trigger_step"] for p in self.future_penalties), default=None),
            "penalties_by_reason": self._group_penalties_by_reason(),
            "total_applied_penalties": self.performance_metrics["delayed_penalties_applied"],
            "total_applied_penalty_amount": self.performance_metrics["total_delayed_penalty"]
        }
    
    def _group_penalties_by_reason(self) -> Dict[str, int]:
        """Group pending penalties by reason type."""
        reason_counts = {}
        for penalty in self.future_penalties:
            reason_type = penalty["reason"].split(" - ")[0]  # Get reason before " - "
            reason_counts[reason_type] = reason_counts.get(reason_type, 0) + 1
        return reason_counts
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            "session_duration": self.current_time,
            "time_remaining": self.time_remaining,
            "energy_remaining": self.energy_budget,
            "metrics": self.performance_metrics.copy(),
            "consequences_triggered": len(self.processed_consequences),
            "pending_consequences": len(self.pending_consequences),
            "total_actions": len(self.action_history),
            "average_score": sum(a["score"] for a in self.action_history) / len(self.action_history) if self.action_history else 0.0,
            "ground_truth_stats": {
                "emails_with_ground_truth": len(self.ground_truth.correct_email_labels),
                "tasks_with_optimal_priorities": len(self.ground_truth.optimal_priorities),
                "scheduled_events": len(self.ground_truth.valid_schedules)
            }
        }


# Global state manager instance
state_manager = StateManager()