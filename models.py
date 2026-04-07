"""Pydantic models for OpsPilot."""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskDifficulty(str, Enum):
    """Task difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GraderType(str, Enum):
    """Available grader types."""
    EMAIL = "email"
    RESPONSE = "response"
    DECISION = "decision"
    FINAL = "final"


class TaskRequest(BaseModel):
    """Request model for task execution."""
    
    task_id: str = Field(..., description="Unique task identifier")
    difficulty: TaskDifficulty = Field(..., description="Task difficulty level")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    
    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Task ID cannot be empty")
        return v.strip()


class TaskResponse(BaseModel):
    """Response model for task execution."""
    
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Task execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class GradingRequest(BaseModel):
    """Request model for grading."""
    
    grader_type: GraderType = Field(..., description="Type of grader to use")
    content: Dict[str, Any] = Field(..., description="Content to grade")
    criteria: Optional[Dict[str, Any]] = Field(default=None, description="Grading criteria")


class GradingResponse(BaseModel):
    """Response model for grading."""
    
    grader_type: GraderType = Field(..., description="Grader type used")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score (0-1)")
    feedback: str = Field(..., description="Grading feedback")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed grading results")
    timestamp: datetime = Field(default_factory=datetime.now, description="Grading timestamp")


class AgentRequest(BaseModel):
    """Request model for agent operations."""
    
    action: str = Field(..., description="Agent action to perform")
    context: Dict[str, Any] = Field(default_factory=dict, description="Action context")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Action cannot be empty")
        return v.strip().lower()


class AgentResponse(BaseModel):
    """Response model for agent operations."""
    
    action: str = Field(..., description="Executed action")
    success: bool = Field(..., description="Operation success status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Operation result")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(default="healthy", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field(default="1.0.0", description="Application version")
    uptime: float = Field(..., description="Uptime in seconds")


# New strongly-typed models for OpsPilot operations

class Email(BaseModel):
    """Email model with customer tier and urgency."""
    
    id: str = Field(..., description="Unique email identifier", min_length=1)
    text: str = Field(..., description="Email content text", min_length=1)
    customer_tier: Literal["free", "premium", "vip"] = Field(..., description="Customer tier level")
    urgency: int = Field(..., description="Hidden ground truth urgency level", ge=1, le=10)
    timestamp: str = Field(..., description="Email timestamp in ISO format")
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Timestamp must be in ISO format")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate email ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Email ID cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "email_001",
                "text": "Dear support, I need help with my account settings.",
                "customer_tier": "premium",
                "urgency": 7,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class Task(BaseModel):
    """Task model with deadline and importance."""
    
    task_id: str = Field(..., description="Unique task identifier", min_length=1)
    description: str = Field(..., description="Task description", min_length=1)
    deadline: int = Field(..., description="Task deadline in minutes from now", ge=0)
    importance: int = Field(..., description="Hidden importance level", ge=1, le=10)
    
    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        """Validate task ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Task ID cannot be empty")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate task description."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Task description cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "description": "Review quarterly financial reports",
                "deadline": 120,
                "importance": 8
            }
        }


class CalendarEvent(BaseModel):
    """Calendar event model with time and duration."""
    
    event_id: str = Field(..., description="Unique event identifier", min_length=1)
    time: int = Field(..., description="Event start time in minutes from now", ge=0)
    duration: int = Field(..., description="Event duration in minutes", ge=1, le=1440)
    
    @field_validator('event_id')
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        """Validate event ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Event ID cannot be empty")
        return v.strip()
    
    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate event duration."""
        if v <= 0:
            raise ValueError("Event duration must be positive")
        if v > 1440:  # 24 hours
            raise ValueError("Event duration cannot exceed 24 hours")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "event_id": "meeting_001",
                "time": 60,
                "duration": 30
            }
        }


class Observation(BaseModel):
    """Observation model containing all current state information."""
    
    emails: List[Email] = Field(default_factory=list, description="List of emails to process")
    tasks: List[Task] = Field(default_factory=list, description="List of tasks to complete")
    calendar: List[CalendarEvent] = Field(default_factory=list, description="List of calendar events")
    time_remaining: int = Field(..., description="Time remaining in minutes", ge=0)
    energy_budget: int = Field(..., description="Available energy budget", ge=0, le=100)
    history: List[str] = Field(default_factory=list, description="History of previous actions")
    
    @field_validator('energy_budget')
    @classmethod
    def validate_energy_budget(cls, v: int) -> int:
        """Validate energy budget range."""
        if v < 0:
            raise ValueError("Energy budget cannot be negative")
        if v > 100:
            raise ValueError("Energy budget cannot exceed 100")
        return v
    
    @field_validator('time_remaining')
    @classmethod
    def validate_time_remaining(cls, v: int) -> int:
        """Validate time remaining."""
        if v < 0:
            raise ValueError("Time remaining cannot be negative")
        return v
    
    @field_validator('history')
    @classmethod
    def validate_history(cls, v: List[str]) -> List[str]:
        """Validate history entries."""
        # Remove empty entries and limit history size
        cleaned_history = [entry.strip() for entry in v if entry and entry.strip()]
        return cleaned_history[-100:]  # Keep only last 100 entries
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "emails": [
                    {
                        "id": "email_001",
                        "text": "Urgent: Server down",
                        "customer_tier": "vip",
                        "urgency": 9,
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                ],
                "tasks": [
                    {
                        "task_id": "task_001",
                        "description": "Fix server issue",
                        "deadline": 30,
                        "importance": 10
                    }
                ],
                "calendar": [
                    {
                        "event_id": "meeting_001",
                        "time": 60,
                        "duration": 30
                    }
                ],
                "time_remaining": 480,
                "energy_budget": 85,
                "history": ["Started work session", "Reviewed emails"]
            }
        }


class Action(BaseModel):
    """Action model containing all possible actions to take."""
    
    email_actions: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of email actions to perform"
    )
    task_priorities: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of task priority assignments"
    )
    scheduling: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of scheduling decisions"
    )
    skip_ids: List[str] = Field(
        default_factory=list, 
        description="List of IDs to skip processing"
    )
    
    @field_validator('email_actions')
    @classmethod
    def validate_email_actions(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate email actions structure."""
        for action in v:
            if not isinstance(action, dict):
                raise ValueError("Each email action must be a dictionary")
            if 'email_id' not in action:
                raise ValueError("Email action must contain 'email_id'")
            if 'action_type' not in action:
                raise ValueError("Email action must contain 'action_type'")
            
            # Validate action_type
            valid_actions = ['reply', 'forward', 'escalate', 'archive', 'defer']
            if action['action_type'] not in valid_actions:
                raise ValueError(f"Invalid action_type. Must be one of: {valid_actions}")
        
        return v
    
    @field_validator('task_priorities')
    @classmethod
    def validate_task_priorities(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate task priorities structure."""
        for priority in v:
            if not isinstance(priority, dict):
                raise ValueError("Each task priority must be a dictionary")
            if 'task_id' not in priority:
                raise ValueError("Task priority must contain 'task_id'")
            if 'priority_level' not in priority:
                raise ValueError("Task priority must contain 'priority_level'")
            
            # Validate priority_level
            if not isinstance(priority['priority_level'], int) or not (1 <= priority['priority_level'] <= 10):
                raise ValueError("Priority level must be an integer between 1 and 10")
        
        return v
    
    @field_validator('scheduling')
    @classmethod
    def validate_scheduling(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate scheduling decisions structure."""
        for schedule in v:
            if not isinstance(schedule, dict):
                raise ValueError("Each scheduling decision must be a dictionary")
            if 'item_id' not in schedule:
                raise ValueError("Scheduling decision must contain 'item_id'")
            if 'scheduled_time' not in schedule:
                raise ValueError("Scheduling decision must contain 'scheduled_time'")
            
            # Validate scheduled_time
            if not isinstance(schedule['scheduled_time'], int) or schedule['scheduled_time'] < 0:
                raise ValueError("Scheduled time must be a non-negative integer")
        
        return v
    
    @field_validator('skip_ids')
    @classmethod
    def validate_skip_ids(cls, v: List[str]) -> List[str]:
        """Validate skip IDs."""
        # Remove empty strings and duplicates
        cleaned_ids = list(set([id_str.strip() for id_str in v if id_str and id_str.strip()]))
        return cleaned_ids
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email_actions": [
                    {
                        "email_id": "email_001",
                        "action_type": "reply",
                        "priority": "high",
                        "estimated_time": 15
                    }
                ],
                "task_priorities": [
                    {
                        "task_id": "task_001",
                        "priority_level": 9,
                        "reason": "Critical system issue"
                    }
                ],
                "scheduling": [
                    {
                        "item_id": "task_001",
                        "scheduled_time": 0,
                        "duration": 45
                    }
                ],
                "skip_ids": ["email_002", "task_003"]
            }
        }


class Reward(BaseModel):
    """Reward model for action evaluation."""
    
    score: float = Field(..., description="Overall reward score", ge=0.0, le=1.0)
    breakdown: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Detailed breakdown of reward components"
    )
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Validate score range."""
        if v < 0.0:
            raise ValueError("Score cannot be negative")
        if v > 1.0:
            raise ValueError("Score cannot exceed 1.0")
        return round(v, 4)  # Round to 4 decimal places
    
    @field_validator('breakdown')
    @classmethod
    def validate_breakdown(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate breakdown structure."""
        if not isinstance(v, dict):
            raise ValueError("Breakdown must be a dictionary")
        
        # Allow negative values for penalties and consequences
        # Only check that the structure is valid
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "score": 0.85,
                "breakdown": {
                    "email_handling": 0.9,
                    "task_prioritization": 0.8,
                    "time_management": 0.85,
                    "energy_efficiency": 0.9,
                    "customer_satisfaction": 0.95,
                    "penalties": {
                        "missed_deadlines": -0.1,
                        "energy_overuse": -0.05
                    },
                    "bonuses": {
                        "vip_customer_priority": 0.1,
                        "early_completion": 0.05
                    }
                }
            }
        }


# Multi-agent models
class EmailAgentAction(BaseModel):
    """Action model for email agent."""
    
    email_actions: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of email actions to perform"
    )
    skip_ids: List[str] = Field(
        default_factory=list, 
        description="List of email IDs to skip processing"
    )
    
    @field_validator('email_actions')
    @classmethod
    def validate_email_actions(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate email actions structure."""
        for action in v:
            if not isinstance(action, dict):
                raise ValueError("Each email action must be a dictionary")
            if 'email_id' not in action:
                raise ValueError("Email action must contain 'email_id'")
            if 'action_type' not in action:
                raise ValueError("Email action must contain 'action_type'")
            
            # Validate action_type
            valid_actions = ['reply', 'forward', 'escalate', 'archive', 'defer']
            if action['action_type'] not in valid_actions:
                raise ValueError(f"Invalid action_type. Must be one of: {valid_actions}")
        
        return v
    
    @field_validator('skip_ids')
    @classmethod
    def validate_skip_ids(cls, v: List[str]) -> List[str]:
        """Validate skip IDs."""
        cleaned_ids = list(set([id_str.strip() for id_str in v if id_str and id_str.strip()]))
        return cleaned_ids


class SchedulerAgentAction(BaseModel):
    """Action model for scheduler agent."""
    
    task_priorities: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of task priority assignments"
    )
    scheduling: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="List of scheduling decisions"
    )
    skip_ids: List[str] = Field(
        default_factory=list, 
        description="List of task/event IDs to skip processing"
    )
    
    @field_validator('task_priorities')
    @classmethod
    def validate_task_priorities(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate task priorities structure."""
        for priority in v:
            if not isinstance(priority, dict):
                raise ValueError("Each task priority must be a dictionary")
            if 'task_id' not in priority:
                raise ValueError("Task priority must contain 'task_id'")
            if 'priority_level' not in priority:
                raise ValueError("Task priority must contain 'priority_level'")
            
            # Validate priority_level
            if not isinstance(priority['priority_level'], int) or not (1 <= priority['priority_level'] <= 10):
                raise ValueError("Priority level must be an integer between 1 and 10")
        
        return v
    
    @field_validator('scheduling')
    @classmethod
    def validate_scheduling(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate scheduling decisions structure."""
        for schedule in v:
            if not isinstance(schedule, dict):
                raise ValueError("Each scheduling decision must be a dictionary")
            if 'item_id' not in schedule:
                raise ValueError("Scheduling decision must contain 'item_id'")
            if 'scheduled_time' not in schedule:
                raise ValueError("Scheduling decision must contain 'scheduled_time'")
            
            # Validate scheduled_time
            if not isinstance(schedule['scheduled_time'], int) or schedule['scheduled_time'] < 0:
                raise ValueError("Scheduled time must be a non-negative integer")
        
        return v
    
    @field_validator('skip_ids')
    @classmethod
    def validate_skip_ids(cls, v: List[str]) -> List[str]:
        """Validate skip IDs."""
        cleaned_ids = list(set([id_str.strip() for id_str in v if id_str and id_str.strip()]))
        return cleaned_ids


class MultiAgentAction(BaseModel):
    """Multi-agent action model supporting both single and multi-agent modes."""
    
    email_agent: Optional[EmailAgentAction] = Field(
        default=None, 
        description="Email agent actions"
    )
    scheduler_agent: Optional[SchedulerAgentAction] = Field(
        default=None, 
        description="Scheduler agent actions"
    )
    
    # Legacy single-agent support (for backward compatibility)
    email_actions: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Legacy: List of email actions to perform"
    )
    task_priorities: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Legacy: List of task priority assignments"
    )
    scheduling: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Legacy: List of scheduling decisions"
    )
    skip_ids: Optional[List[str]] = Field(
        default=None, 
        description="Legacy: List of IDs to skip processing"
    )
    
    @model_validator(mode='before')
    @classmethod
    def validate_multi_agent_structure(cls, values):
        """Validate multi-agent structure."""
        # Check if this is multi-agent mode
        email_agent = values.get('email_agent')
        scheduler_agent = values.get('scheduler_agent')
        
        # Legacy fields
        email_actions = values.get('email_actions')
        task_priorities = values.get('task_priorities')
        scheduling = values.get('scheduling')
        skip_ids = values.get('skip_ids')
        
        # Determine if we're in multi-agent or single-agent mode
        has_multi_agent = email_agent is not None or scheduler_agent is not None
        has_legacy = any([email_actions, task_priorities, scheduling, skip_ids])
        
        if has_multi_agent and has_legacy:
            raise ValueError("Cannot mix multi-agent and legacy single-agent action formats")
        
        # Ensure at least one agent is specified in multi-agent mode
        if has_multi_agent and not (email_agent or scheduler_agent):
            raise ValueError("At least one agent must be specified in multi-agent mode")
        
        return values
    
    def is_multi_agent(self) -> bool:
        """Check if this is a multi-agent action."""
        return self.email_agent is not None or self.scheduler_agent is not None
    
    def to_legacy_action(self) -> 'Action':
        """Convert to legacy Action format for backward compatibility."""
        if self.is_multi_agent():
            # Combine multi-agent actions into legacy format
            email_actions = self.email_agent.email_actions if self.email_agent else []
            task_priorities = self.scheduler_agent.task_priorities if self.scheduler_agent else []
            scheduling = self.scheduler_agent.scheduling if self.scheduler_agent else []
            
            # Combine skip_ids from both agents
            skip_ids = []
            if self.email_agent:
                skip_ids.extend(self.email_agent.skip_ids)
            if self.scheduler_agent:
                skip_ids.extend(self.scheduler_agent.skip_ids)
            
            return Action(
                email_actions=email_actions,
                task_priorities=task_priorities,
                scheduling=scheduling,
                skip_ids=list(set(skip_ids))  # Remove duplicates
            )
        else:
            # Use legacy fields directly
            return Action(
                email_actions=self.email_actions or [],
                task_priorities=self.task_priorities or [],
                scheduling=self.scheduling or [],
                skip_ids=self.skip_ids or []
            )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email_agent": {
                    "email_actions": [
                        {
                            "email_id": "email_001",
                            "action_type": "reply",
                            "priority": "high"
                        }
                    ],
                    "skip_ids": ["email_002"]
                },
                "scheduler_agent": {
                    "task_priorities": [
                        {
                            "task_id": "task_001",
                            "priority_level": 9
                        }
                    ],
                    "scheduling": [
                        {
                            "item_id": "task_001",
                            "scheduled_time": 30,
                            "duration": 45
                        }
                    ],
                    "skip_ids": ["task_002"]
                }
            }
        }


# Enhanced request/response models for the new system

class ObservationRequest(BaseModel):
    """Request model for getting current observation."""
    
    include_history: bool = Field(default=True, description="Whether to include action history")
    max_history_items: int = Field(default=50, description="Maximum history items to return", ge=1, le=100)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "include_history": True,
                "max_history_items": 50
            }
        }


class ActionRequest(BaseModel):
    """Request model for submitting actions."""
    
    observation_id: str = Field(..., description="ID of the observation this action responds to")
    action: Action = Field(..., description="Action to take")
    reasoning: Optional[str] = Field(default=None, description="Optional reasoning for the action")
    
    @field_validator('observation_id')
    @classmethod
    def validate_observation_id(cls, v: str) -> str:
        """Validate observation ID."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Observation ID cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "observation_id": "obs_001",
                "action": {
                    "email_actions": [
                        {
                            "email_id": "email_001",
                            "action_type": "reply",
                            "priority": "high"
                        }
                    ],
                    "task_priorities": [
                        {
                            "task_id": "task_001",
                            "priority_level": 9
                        }
                    ],
                    "scheduling": [],
                    "skip_ids": []
                },
                "reasoning": "Prioritizing VIP customer email and critical system task"
            }
        }


class ActionResponse(BaseModel):
    """Response model for action submission."""
    
    action_id: str = Field(..., description="Unique action identifier")
    accepted: bool = Field(..., description="Whether the action was accepted")
    reward: Optional[Reward] = Field(default=None, description="Reward for the action")
    feedback: str = Field(default="", description="Feedback on the action")
    next_observation_id: Optional[str] = Field(default=None, description="ID of the next observation")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "action_id": "action_001",
                "accepted": True,
                "reward": {
                    "score": 0.85,
                    "breakdown": {
                        "email_handling": 0.9,
                        "task_prioritization": 0.8
                    }
                },
                "feedback": "Good prioritization of VIP customer needs",
                "next_observation_id": "obs_002"
            }
        }