"""Baseline agent implementation for OpsPilot."""

import random
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from models import Action, Email, Task, CalendarEvent, Observation


class BaselineAgent:
    """
    Baseline agent for OpsPilot operations.
    
    Implements simple rule-based behavior:
    - Classify emails using simple rules
    - Generate short polite responses
    - Prioritize VIP + urgent items
    - Schedule sequentially
    """
    
    def __init__(self, random_seed: Optional[int] = None) -> None:
        """Initialize baseline agent with deterministic behavior."""
        self.random_seed = random_seed or 42
        random.seed(self.random_seed)
        
        self.agent_id = f"baseline_agent_{self.random_seed}"
        self.action_count = 0
        self.start_time = datetime.now()
        
        # Email classification rules
        self.urgency_keywords = {
            "high": ["urgent", "asap", "emergency", "critical", "immediate", "help", "problem", "issue", "broken", "down"],
            "medium": ["soon", "important", "needed", "request", "question", "support"],
            "low": ["when", "possible", "convenient", "update", "info", "fyi"]
        }
        
        # Customer tier indicators
        self.vip_indicators = ["vip", "premium", "enterprise", "priority", "executive", "director", "ceo", "manager"]
        self.free_indicators = ["free", "trial", "basic", "standard"]
        
        # Response templates
        self.response_templates = {
            "vip_urgent": [
                "Thank you for contacting us. I understand this is urgent and will prioritize your request immediately.",
                "I apologize for any inconvenience. As a valued customer, I will personally ensure this is resolved quickly.",
                "Thank you for reaching out. I will escalate this to our priority support team right away."
            ],
            "vip_normal": [
                "Thank you for your message. As a valued customer, I will ensure this receives prompt attention.",
                "I appreciate you contacting us. I will personally handle your request and provide an update soon.",
                "Thank you for reaching out. I will prioritize this and get back to you with a solution."
            ],
            "urgent": [
                "Thank you for contacting us. I understand this is urgent and will address it as quickly as possible.",
                "I see this requires immediate attention. I will work on this right away and keep you updated.",
                "Thank you for your message. I will prioritize this urgent matter and respond promptly."
            ],
            "normal": [
                "Thank you for contacting us. I will review your request and provide a response soon.",
                "I appreciate you reaching out. I will look into this and get back to you with more information.",
                "Thank you for your message. I will address your inquiry and respond as soon as possible."
            ],
            "low": [
                "Thank you for your message. I will review this when I have a chance and follow up accordingly.",
                "I appreciate you contacting us. I will add this to my queue and respond when possible.",
                "Thank you for reaching out. I will look into this and provide an update in due course."
            ]
        }
    
    def execute_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an agent action.
        
        Args:
            action: Action to execute
            context: Action context and parameters
            
        Returns:
            Action execution result
        """
        self.action_count += 1
        start_time = datetime.now()
        
        try:
            if action == "generate_action":
                result = self._generate_action(context)
            elif action == "classify_email":
                result = self._classify_email(context)
            elif action == "generate_response":
                result = self._generate_response(context)
            elif action == "prioritize_tasks":
                result = self._prioritize_tasks(context)
            elif action == "schedule_items":
                result = self._schedule_items(context)
            else:
                result = self._default_action(action, context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "action": action,
                "result": result,
                "agent_id": self.agent_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "agent_id": self.agent_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete action based on observation."""
        observation_data = context.get("observation", {})
        
        # Parse observation
        emails = observation_data.get("emails", [])
        tasks = observation_data.get("tasks", [])
        calendar_events = observation_data.get("calendar_events", [])
        current_time = observation_data.get("current_time", 0)
        time_remaining = observation_data.get("time_remaining", 480)
        energy_budget = observation_data.get("energy_budget", 100)
        
        # Generate email actions
        email_actions = []
        for email in emails:
            email_action = self._process_email(email)
            if email_action:
                email_actions.append(email_action)
        
        # Generate task priorities
        task_priorities = []
        for task in tasks:
            priority = self._calculate_task_priority(task, emails)
            task_priorities.append({
                "task_id": task.get("task_id", task.get("id", "unknown")),
                "priority_level": priority
            })
        
        # Generate scheduling
        scheduling = self._generate_scheduling(tasks, calendar_events, current_time, time_remaining)
        
        # Determine items to skip (low priority items when time/energy is limited)
        skip_ids = self._determine_skip_items(emails, tasks, time_remaining, energy_budget)
        
        action = Action(
            email_actions=email_actions,
            task_priorities=task_priorities,
            scheduling=scheduling,
            skip_ids=skip_ids
        )
        
        reasoning = self._generate_reasoning(emails, tasks, time_remaining, energy_budget)
        
        return {
            "action": action.model_dump(),
            "reasoning": reasoning,
            "confidence": self._calculate_confidence(emails, tasks),
            "strategy": "vip_urgent_first"
        }
    
    def _process_email(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single email and generate action."""
        email_id = email.get("id", email.get("email_id", "unknown"))
        email_text = email.get("text", email.get("content", ""))
        customer_tier = email.get("customer_tier", "free")
        urgency = email.get("urgency", 5)
        
        # Classify email
        classification = self._classify_email_content(email_text, customer_tier, urgency)
        
        # Generate response
        response_content = self._generate_email_response(email_text, customer_tier, urgency, classification)
        
        # Determine action type
        if urgency >= 8 or customer_tier == "vip":
            action_type = "reply"
        elif urgency >= 6:
            action_type = "reply"
        elif urgency <= 3:
            action_type = "defer"
        else:
            action_type = "reply"
        
        return {
            "email_id": email_id,
            "action_type": action_type,
            "response_content": response_content,
            "priority": "high" if (urgency >= 7 or customer_tier == "vip") else "normal",
            "estimated_time": 15 if customer_tier == "vip" else 10
        }
    
    def _classify_email_content(self, email_text: str, customer_tier: str, urgency: int) -> Dict[str, Any]:
        """Classify email using simple rules."""
        text_lower = email_text.lower()
        
        # Determine urgency based on keywords
        detected_urgency = 5  # Default
        
        high_urgency_count = sum(1 for keyword in self.urgency_keywords["high"] if keyword in text_lower)
        medium_urgency_count = sum(1 for keyword in self.urgency_keywords["medium"] if keyword in text_lower)
        low_urgency_count = sum(1 for keyword in self.urgency_keywords["low"] if keyword in text_lower)
        
        if high_urgency_count > 0:
            detected_urgency = min(10, 7 + high_urgency_count)
        elif medium_urgency_count > 0:
            detected_urgency = 5 + medium_urgency_count
        elif low_urgency_count > 0:
            detected_urgency = max(1, 4 - low_urgency_count)
        
        # Detect customer tier from content
        detected_tier = customer_tier
        if any(indicator in text_lower for indicator in self.vip_indicators):
            detected_tier = "vip"
        elif any(indicator in text_lower for indicator in self.free_indicators):
            detected_tier = "free"
        
        # Determine category
        if "question" in text_lower or "?" in email_text:
            category = "inquiry"
        elif any(word in text_lower for word in ["problem", "issue", "error", "broken", "not working"]):
            category = "support"
        elif any(word in text_lower for word in ["complaint", "unhappy", "disappointed", "frustrated"]):
            category = "complaint"
        elif any(word in text_lower for word in ["thank", "thanks", "appreciate"]):
            category = "feedback"
        else:
            category = "general"
        
        return {
            "detected_urgency": detected_urgency,
            "detected_tier": detected_tier,
            "category": category,
            "confidence": 0.8
        }
    
    def _generate_email_response(self, email_text: str, customer_tier: str, urgency: int, classification: Dict[str, Any]) -> str:
        """Generate a short polite response."""
        # Determine response template category
        if customer_tier == "vip" and urgency >= 7:
            template_category = "vip_urgent"
        elif customer_tier == "vip":
            template_category = "vip_normal"
        elif urgency >= 7:
            template_category = "urgent"
        elif urgency <= 3:
            template_category = "low"
        else:
            template_category = "normal"
        
        # Select template
        templates = self.response_templates[template_category]
        base_response = random.choice(templates)
        
        # Add specific context if needed
        category = classification.get("category", "general")
        if category == "support":
            base_response += " I will investigate this technical issue and provide a solution."
        elif category == "complaint":
            base_response += " I sincerely apologize for any inconvenience caused."
        elif category == "inquiry":
            base_response += " I will gather the information you requested and respond shortly."
        
        # Keep response concise (under 150 characters for baseline)
        if len(base_response) > 150:
            base_response = base_response[:147] + "..."
        
        return base_response
    
    def _calculate_task_priority(self, task: Dict[str, Any], emails: List[Dict[str, Any]]) -> int:
        """Calculate task priority level (1-10)."""
        importance = task.get("importance", 5)
        deadline = task.get("deadline", 480)  # Default 8 hours
        
        # Base priority from importance
        priority = importance
        
        # Adjust for deadline urgency
        if deadline <= 60:  # 1 hour
            priority = min(10, priority + 3)
        elif deadline <= 120:  # 2 hours
            priority = min(10, priority + 2)
        elif deadline <= 240:  # 4 hours
            priority = min(10, priority + 1)
        
        # Boost priority if related to VIP emails
        task_description = task.get("description", "").lower()
        for email in emails:
            if email.get("customer_tier") == "vip":
                email_text = email.get("text", "").lower()
                # Simple keyword matching
                common_words = set(task_description.split()) & set(email_text.split())
                if len(common_words) > 2:
                    priority = min(10, priority + 1)
                    break
        
        return max(1, min(10, priority))
    
    def _generate_scheduling(self, tasks: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], 
                           current_time: int, time_remaining: int) -> List[Dict[str, Any]]:
        """Generate sequential scheduling for tasks."""
        scheduling = []
        
        # Sort tasks by priority (calculated earlier)
        sorted_tasks = sorted(tasks, key=lambda t: self._calculate_task_priority(t, []), reverse=True)
        
        # Get existing event times to avoid conflicts
        occupied_times = []
        for event in calendar_events:
            start_time = event.get("time", 0)
            duration = event.get("duration", 60)
            occupied_times.append((start_time, start_time + duration))
        
        # Schedule tasks sequentially
        current_schedule_time = current_time + 30  # Start 30 minutes from now
        
        for task in sorted_tasks[:5]:  # Limit to top 5 tasks
            task_id = task.get("task_id", task.get("id", "unknown"))
            estimated_duration = task.get("estimated_duration", 60)
            deadline = task.get("deadline", time_remaining)
            
            # Find next available slot
            scheduled_time = self._find_next_available_slot(
                current_schedule_time, estimated_duration, occupied_times, deadline
            )
            
            if scheduled_time is not None and scheduled_time < time_remaining:
                scheduling.append({
                    "item_id": task_id,
                    "scheduled_time": scheduled_time,
                    "duration": estimated_duration,
                    "priority": self._calculate_task_priority(task, []),
                    "deadline": deadline,
                    "item_type": "task"
                })
                
                # Update occupied times and current schedule time
                occupied_times.append((scheduled_time, scheduled_time + estimated_duration))
                current_schedule_time = scheduled_time + estimated_duration + 15  # 15 min buffer
        
        return scheduling
    
    def _find_next_available_slot(self, start_time: int, duration: int, 
                                occupied_times: List[Tuple[int, int]], deadline: int) -> Optional[int]:
        """Find next available time slot for scheduling."""
        current_time = start_time
        
        while current_time + duration <= deadline:
            # Check if this slot conflicts with existing events
            slot_end = current_time + duration
            conflict = False
            
            for occupied_start, occupied_end in occupied_times:
                if (current_time < occupied_end and slot_end > occupied_start):
                    conflict = True
                    current_time = occupied_end + 15  # Move past conflict with buffer
                    break
            
            if not conflict:
                return current_time
        
        return None  # No available slot found
    
    def _determine_skip_items(self, emails: List[Dict[str, Any]], tasks: List[Dict[str, Any]], 
                            time_remaining: int, energy_budget: int) -> List[str]:
        """Determine which items to skip based on constraints."""
        skip_ids = []
        
        # Skip low priority items if time/energy is limited
        if time_remaining < 120 or energy_budget < 30:  # Less than 2 hours or low energy
            # Skip low urgency emails
            for email in emails:
                if email.get("urgency", 5) <= 3 and email.get("customer_tier") != "vip":
                    skip_ids.append(email.get("id", email.get("email_id", "")))
            
            # Skip low importance tasks
            for task in tasks:
                if task.get("importance", 5) <= 3:
                    skip_ids.append(task.get("task_id", task.get("id", "")))
        
        return [skip_id for skip_id in skip_ids if skip_id]  # Remove empty strings
    
    def _generate_reasoning(self, emails: List[Dict[str, Any]], tasks: List[Dict[str, Any]], 
                          time_remaining: int, energy_budget: int) -> str:
        """Generate reasoning for the action taken."""
        reasoning_parts = []
        
        # Email handling reasoning
        vip_emails = [e for e in emails if e.get("customer_tier") == "vip"]
        urgent_emails = [e for e in emails if e.get("urgency", 5) >= 7]
        
        if vip_emails:
            reasoning_parts.append(f"Prioritizing {len(vip_emails)} VIP customer emails for immediate response")
        
        if urgent_emails:
            reasoning_parts.append(f"Addressing {len(urgent_emails)} urgent emails with high priority")
        
        # Task prioritization reasoning
        high_priority_tasks = [t for t in tasks if t.get("importance", 5) >= 7]
        if high_priority_tasks:
            reasoning_parts.append(f"Focusing on {len(high_priority_tasks)} high-importance tasks")
        
        # Resource constraints
        if time_remaining < 240:  # Less than 4 hours
            reasoning_parts.append("Optimizing for limited time remaining")
        
        if energy_budget < 50:
            reasoning_parts.append("Conserving energy for critical tasks")
        
        # Default reasoning
        if not reasoning_parts:
            reasoning_parts.append("Following standard prioritization: VIP customers first, then urgency-based handling")
        
        return ". ".join(reasoning_parts) + "."
    
    def _calculate_confidence(self, emails: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the action."""
        base_confidence = 0.7
        
        # Higher confidence with clear priorities
        vip_count = len([e for e in emails if e.get("customer_tier") == "vip"])
        urgent_count = len([e for e in emails if e.get("urgency", 5) >= 7])
        
        if vip_count > 0 or urgent_count > 0:
            base_confidence += 0.1
        
        # Lower confidence with many items
        total_items = len(emails) + len(tasks)
        if total_items > 10:
            base_confidence -= 0.1
        elif total_items < 3:
            base_confidence += 0.1
        
        return max(0.5, min(1.0, base_confidence))
    
    def _classify_email(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single email."""
        email_text = context.get("email_text", "")
        customer_tier = context.get("customer_tier", "free")
        urgency = context.get("urgency", 5)
        
        return self._classify_email_content(email_text, customer_tier, urgency)
    
    def _generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for a single email."""
        email_text = context.get("email_text", "")
        customer_tier = context.get("customer_tier", "free")
        urgency = context.get("urgency", 5)
        
        classification = self._classify_email_content(email_text, customer_tier, urgency)
        response = self._generate_email_response(email_text, customer_tier, urgency, classification)
        
        return {
            "response": response,
            "classification": classification,
            "response_length": len(response)
        }
    
    def _prioritize_tasks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize a list of tasks."""
        tasks = context.get("tasks", [])
        emails = context.get("emails", [])
        
        prioritized_tasks = []
        for task in tasks:
            priority = self._calculate_task_priority(task, emails)
            prioritized_tasks.append({
                "task": task,
                "priority": priority
            })
        
        # Sort by priority
        prioritized_tasks.sort(key=lambda x: x["priority"], reverse=True)
        
        return {
            "prioritized_tasks": prioritized_tasks,
            "total_tasks": len(tasks),
            "method": "importance_deadline_vip"
        }
    
    def _schedule_items(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule items sequentially."""
        tasks = context.get("tasks", [])
        calendar_events = context.get("calendar_events", [])
        current_time = context.get("current_time", 0)
        time_remaining = context.get("time_remaining", 480)
        
        scheduling = self._generate_scheduling(tasks, calendar_events, current_time, time_remaining)
        
        return {
            "scheduling": scheduling,
            "total_scheduled": len(scheduling),
            "method": "sequential_priority"
        }
    
    def _default_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown actions."""
        return {
            "message": f"Action '{action}' not recognized",
            "available_actions": [
                "generate_action",
                "classify_email",
                "generate_response",
                "prioritize_tasks",
                "schedule_items"
            ],
            "context_received": bool(context)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "agent_id": self.agent_id,
            "agent_type": "baseline",
            "random_seed": self.random_seed,
            "action_count": self.action_count,
            "uptime_seconds": uptime,
            "capabilities": [
                "email_classification",
                "response_generation", 
                "task_prioritization",
                "sequential_scheduling",
                "vip_urgent_prioritization"
            ],
            "strategy": "rule_based_deterministic",
            "start_time": self.start_time.isoformat()
        }
    
    def reset(self) -> None:
        """Reset agent state."""
        random.seed(self.random_seed)
        self.action_count = 0
        self.start_time = datetime.now()