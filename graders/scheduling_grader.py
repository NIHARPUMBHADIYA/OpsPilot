"""Deterministic scheduling grader for OpsPilot - evaluates scheduling efficiency and conflict avoidance."""

from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime


class SchedulingGrader:
    """Deterministic grader for scheduling quality based on conflict avoidance and efficiency."""
    
    def __init__(self) -> None:
        """Initialize scheduling grader."""
        self.grader_type = "scheduling"
        self.max_score = 1.0
        
        # Define scoring weights
        self.scoring_weights = {
            "conflict_avoidance": 0.4,    # No overlapping events (most critical)
            "deadline_placement": 0.35,   # Correct placement near deadlines
            "time_efficiency": 0.25       # Efficient time usage, minimal waste
        }
        
        # Define thresholds
        self.deadline_buffer_optimal = 60    # Optimal buffer before deadline (minutes)
        self.deadline_buffer_acceptable = 30 # Acceptable buffer before deadline
        self.max_gap_penalty = 120          # Maximum gap between events before penalty
        self.min_event_duration = 15        # Minimum reasonable event duration
    
    def grade(self, scheduled_events: List[Dict[str, Any]], 
              deadlines: Dict[str, int],
              time_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade scheduling quality based on conflict avoidance and efficiency.
        
        Args:
            scheduled_events: List of scheduled events
                Format: [
                    {
                        "item_id": str,
                        "item_type": str,  # "task", "email", "meeting"
                        "scheduled_time": int,  # Start time in minutes
                        "duration": int,        # Duration in minutes
                        "priority": int,        # Priority level (1-10)
                        "deadline": int         # Deadline in minutes (optional)
                    }
                ]
            deadlines: Dict mapping item_id to deadline in minutes
                Format: {"item_id": deadline_minutes}
            time_constraints: Overall time constraints
                Format: {
                    "total_time_available": int,  # Total available time
                    "current_time": int,          # Current time offset
                    "existing_events": [          # Pre-existing calendar events
                        {"start_time": int, "end_time": int, "event_id": str}
                    ]
                }
                
        Returns:
            Grading result with score between 0-1 and detailed breakdown
        """
        if not scheduled_events:
            return self._create_empty_result("No scheduled events to evaluate")
        
        # Grade each component
        conflict_score, conflict_details = self._grade_conflict_avoidance(
            scheduled_events, time_constraints.get("existing_events", [])
        )
        
        deadline_score, deadline_details = self._grade_deadline_placement(
            scheduled_events, deadlines
        )
        
        efficiency_score, efficiency_details = self._grade_time_efficiency(
            scheduled_events, time_constraints
        )
        
        # Calculate weighted final score
        final_score = (
            conflict_score * self.scoring_weights["conflict_avoidance"] +
            deadline_score * self.scoring_weights["deadline_placement"] +
            efficiency_score * self.scoring_weights["time_efficiency"]
        )
        
        # Generate feedback
        feedback = self._generate_feedback(conflict_score, deadline_score, efficiency_score, final_score)
        
        return {
            "score": min(final_score, self.max_score),
            "feedback": feedback,
            "details": {
                "component_scores": {
                    "conflict_avoidance": conflict_score,
                    "deadline_placement": deadline_score,
                    "time_efficiency": efficiency_score
                },
                "breakdown": {
                    "conflict_avoidance": conflict_details,
                    "deadline_placement": deadline_details,
                    "time_efficiency": efficiency_details
                },
                "weights_used": self.scoring_weights,
                "total_events_scheduled": len(scheduled_events)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _grade_conflict_avoidance(self, scheduled_events: List[Dict[str, Any]], 
                                 existing_events: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Grade how well the schedule avoids conflicts and overlaps."""
        if not scheduled_events:
            return 1.0, {"reason": "No events to check for conflicts"}
        
        # Convert events to time intervals for easier conflict detection
        scheduled_intervals = []
        for event in scheduled_events:
            start_time = event.get("scheduled_time", 0)
            duration = event.get("duration", 0)
            end_time = start_time + duration
            scheduled_intervals.append({
                "item_id": event.get("item_id", "unknown"),
                "start": start_time,
                "end": end_time,
                "priority": event.get("priority", 5)
            })
        
        existing_intervals = []
        for event in existing_events:
            existing_intervals.append({
                "event_id": event.get("event_id", "existing"),
                "start": event.get("start_time", 0),
                "end": event.get("end_time", 0)
            })
        
        # Check for conflicts between scheduled events
        scheduled_conflicts = self._find_conflicts(scheduled_intervals, scheduled_intervals)
        
        # Check for conflicts with existing events
        existing_conflicts = self._find_conflicts(scheduled_intervals, existing_intervals)
        
        total_conflicts = len(scheduled_conflicts) + len(existing_conflicts)
        total_possible_conflicts = len(scheduled_events) * (len(scheduled_events) - 1) // 2
        total_possible_conflicts += len(scheduled_events) * len(existing_events)
        
        # Calculate conflict-free score
        if total_possible_conflicts == 0:
            conflict_free_score = 1.0
        else:
            conflict_free_score = max(0.0, 1.0 - (total_conflicts / max(total_possible_conflicts, 1)))
        
        # Penalty for high-priority conflicts
        priority_penalty = self._calculate_priority_conflict_penalty(scheduled_conflicts, scheduled_intervals)
        
        final_score = max(0.0, conflict_free_score - priority_penalty)
        
        details = {
            "total_conflicts": total_conflicts,
            "scheduled_conflicts": len(scheduled_conflicts),
            "existing_conflicts": len(existing_conflicts),
            "conflict_free_score": conflict_free_score,
            "priority_penalty": priority_penalty,
            "conflict_details": scheduled_conflicts + existing_conflicts
        }
        
        return min(final_score, 1.0), details
    
    def _grade_deadline_placement(self, scheduled_events: List[Dict[str, Any]], 
                                 deadlines: Dict[str, int]) -> Tuple[float, Dict[str, Any]]:
        """Grade how well events are placed relative to their deadlines."""
        if not deadlines:
            return 0.8, {"reason": "No deadlines provided for evaluation"}
        
        placement_scores = []
        placement_details = []
        
        for event in scheduled_events:
            item_id = event.get("item_id")
            scheduled_time = event.get("scheduled_time", 0)
            duration = event.get("duration", 0)
            completion_time = scheduled_time + duration
            
            deadline = deadlines.get(item_id)
            if deadline is None:
                # No deadline for this item - neutral score
                placement_scores.append(0.7)
                placement_details.append({
                    "item_id": item_id,
                    "status": "no_deadline",
                    "score": 0.7
                })
                continue
            
            # Calculate time buffer before deadline
            time_buffer = deadline - completion_time
            
            if time_buffer < 0:
                # Scheduled after deadline - major penalty
                score = 0.0
                status = "past_deadline"
            elif time_buffer <= self.deadline_buffer_acceptable:
                # Very close to deadline - risky but acceptable
                score = 0.6
                status = "tight_deadline"
            elif time_buffer <= self.deadline_buffer_optimal:
                # Good buffer time
                score = 0.9
                status = "good_buffer"
            else:
                # Optimal buffer time
                score = 1.0
                status = "optimal_buffer"
            
            placement_scores.append(score)
            placement_details.append({
                "item_id": item_id,
                "scheduled_time": scheduled_time,
                "completion_time": completion_time,
                "deadline": deadline,
                "time_buffer": time_buffer,
                "status": status,
                "score": score
            })
        
        # Calculate average placement score
        avg_score = sum(placement_scores) / len(placement_scores) if placement_scores else 0.0
        
        # Bonus for prioritizing urgent deadlines
        urgency_bonus = self._calculate_urgency_bonus(scheduled_events, deadlines)
        
        final_score = min(avg_score + urgency_bonus, 1.0)
        
        details = {
            "average_placement_score": avg_score,
            "urgency_bonus": urgency_bonus,
            "placement_details": placement_details,
            "events_with_deadlines": len([d for d in placement_details if d["status"] != "no_deadline"])
        }
        
        return final_score, details
    
    def _grade_time_efficiency(self, scheduled_events: List[Dict[str, Any]], 
                              time_constraints: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Grade efficient use of available time and minimal waste."""
        if not scheduled_events:
            return 0.5, {"reason": "No events to evaluate for efficiency"}
        
        total_available_time = time_constraints.get("total_time_available", 480)  # Default 8 hours
        current_time = time_constraints.get("current_time", 0)
        
        # Calculate time utilization
        total_scheduled_time = sum(event.get("duration", 0) for event in scheduled_events)
        utilization_ratio = total_scheduled_time / total_available_time if total_available_time > 0 else 0
        
        # Optimal utilization is 70-85% (allows for breaks and flexibility)
        if 0.70 <= utilization_ratio <= 0.85:
            utilization_score = 1.0
        elif 0.60 <= utilization_ratio <= 0.90:
            utilization_score = 0.8
        elif 0.50 <= utilization_ratio <= 0.95:
            utilization_score = 0.6
        else:
            utilization_score = 0.4  # Too low or too high utilization
        
        # Check for time gaps and clustering
        gap_penalty = self._calculate_gap_penalty(scheduled_events)
        
        # Check for appropriate event durations
        duration_score = self._calculate_duration_appropriateness(scheduled_events)
        
        # Check for logical ordering (high priority items scheduled earlier)
        ordering_score = self._calculate_priority_ordering_score(scheduled_events)
        
        # Combine efficiency metrics
        efficiency_score = (
            utilization_score * 0.4 +
            (1.0 - gap_penalty) * 0.3 +
            duration_score * 0.2 +
            ordering_score * 0.1
        )
        
        details = {
            "utilization_ratio": utilization_ratio,
            "utilization_score": utilization_score,
            "gap_penalty": gap_penalty,
            "duration_score": duration_score,
            "ordering_score": ordering_score,
            "total_scheduled_time": total_scheduled_time,
            "total_available_time": total_available_time
        }
        
        return min(efficiency_score, 1.0), details
    
    def _find_conflicts(self, intervals1: List[Dict[str, Any]], 
                       intervals2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find overlapping intervals between two lists."""
        conflicts = []
        
        for i, interval1 in enumerate(intervals1):
            for j, interval2 in enumerate(intervals2):
                # Skip self-comparison
                if intervals1 is intervals2 and i >= j:
                    continue
                
                # Check for overlap
                if (interval1["start"] < interval2["end"] and 
                    interval1["end"] > interval2["start"]):
                    
                    overlap_start = max(interval1["start"], interval2["start"])
                    overlap_end = min(interval1["end"], interval2["end"])
                    overlap_duration = overlap_end - overlap_start
                    
                    conflicts.append({
                        "item1": interval1.get("item_id", interval1.get("event_id")),
                        "item2": interval2.get("item_id", interval2.get("event_id")),
                        "overlap_start": overlap_start,
                        "overlap_end": overlap_end,
                        "overlap_duration": overlap_duration
                    })
        
        return conflicts
    
    def _calculate_priority_conflict_penalty(self, conflicts: List[Dict[str, Any]], 
                                           intervals: List[Dict[str, Any]]) -> float:
        """Calculate additional penalty for conflicts involving high-priority items."""
        penalty = 0.0
        
        for conflict in conflicts:
            item1_id = conflict["item1"]
            item2_id = conflict["item2"]
            
            # Find priority levels
            item1_priority = 5  # Default priority
            item2_priority = 5
            
            for interval in intervals:
                if interval.get("item_id") == item1_id:
                    item1_priority = interval.get("priority", 5)
                elif interval.get("item_id") == item2_id:
                    item2_priority = interval.get("priority", 5)
            
            # Higher penalty for high-priority conflicts
            max_priority = max(item1_priority, item2_priority)
            if max_priority >= 8:
                penalty += 0.2
            elif max_priority >= 6:
                penalty += 0.1
            else:
                penalty += 0.05
        
        return min(penalty, 0.5)  # Cap penalty at 0.5
    
    def _calculate_urgency_bonus(self, scheduled_events: List[Dict[str, Any]], 
                                deadlines: Dict[str, int]) -> float:
        """Calculate bonus for properly prioritizing urgent deadlines."""
        bonus = 0.0
        
        # Find events with urgent deadlines (within 2 hours)
        urgent_events = []
        for event in scheduled_events:
            item_id = event.get("item_id")
            deadline = deadlines.get(item_id)
            if deadline and deadline <= 120:  # Within 2 hours
                urgent_events.append({
                    "item_id": item_id,
                    "scheduled_time": event.get("scheduled_time", 0),
                    "deadline": deadline
                })
        
        if not urgent_events:
            return 0.0
        
        # Check if urgent events are scheduled early
        urgent_events.sort(key=lambda x: x["scheduled_time"])
        
        for i, event in enumerate(urgent_events):
            # Earlier scheduling of urgent items gets bonus
            if i == 0:  # First urgent event
                bonus += 0.1
            elif i == 1:  # Second urgent event
                bonus += 0.05
        
        return min(bonus, 0.15)  # Cap bonus at 0.15
    
    def _calculate_gap_penalty(self, scheduled_events: List[Dict[str, Any]]) -> float:
        """Calculate penalty for inefficient gaps between events."""
        if len(scheduled_events) < 2:
            return 0.0
        
        # Sort events by start time
        sorted_events = sorted(scheduled_events, key=lambda x: x.get("scheduled_time", 0))
        
        penalty = 0.0
        total_gaps = 0
        
        for i in range(len(sorted_events) - 1):
            current_end = sorted_events[i].get("scheduled_time", 0) + sorted_events[i].get("duration", 0)
            next_start = sorted_events[i + 1].get("scheduled_time", 0)
            gap = next_start - current_end
            
            if gap > self.max_gap_penalty:
                # Large gap - penalty
                penalty += 0.1
                total_gaps += 1
            elif gap < 0:
                # Overlap - already handled in conflict detection
                pass
        
        return min(penalty, 0.3)  # Cap penalty at 0.3
    
    def _calculate_duration_appropriateness(self, scheduled_events: List[Dict[str, Any]]) -> float:
        """Calculate score for appropriate event durations."""
        if not scheduled_events:
            return 1.0
        
        appropriate_durations = 0
        
        for event in scheduled_events:
            duration = event.get("duration", 0)
            item_type = event.get("item_type", "task")
            
            # Check duration appropriateness by type
            if item_type == "email":
                # Emails should be 15-45 minutes
                if 15 <= duration <= 45:
                    appropriate_durations += 1
                elif 10 <= duration <= 60:
                    appropriate_durations += 0.7
                else:
                    appropriate_durations += 0.3
            elif item_type == "task":
                # Tasks should be 30-180 minutes
                if 30 <= duration <= 180:
                    appropriate_durations += 1
                elif 15 <= duration <= 240:
                    appropriate_durations += 0.8
                else:
                    appropriate_durations += 0.4
            elif item_type == "meeting":
                # Meetings should be 30-120 minutes
                if 30 <= duration <= 120:
                    appropriate_durations += 1
                elif 15 <= duration <= 180:
                    appropriate_durations += 0.8
                else:
                    appropriate_durations += 0.4
            else:
                # Unknown type - neutral score
                appropriate_durations += 0.7
        
        return appropriate_durations / len(scheduled_events)
    
    def _calculate_priority_ordering_score(self, scheduled_events: List[Dict[str, Any]]) -> float:
        """Calculate score for logical priority-based ordering."""
        if len(scheduled_events) < 2:
            return 1.0
        
        # Sort events by scheduled time
        sorted_events = sorted(scheduled_events, key=lambda x: x.get("scheduled_time", 0))
        
        correct_orderings = 0
        total_comparisons = 0
        
        for i in range(len(sorted_events) - 1):
            current_priority = sorted_events[i].get("priority", 5)
            next_priority = sorted_events[i + 1].get("priority", 5)
            
            total_comparisons += 1
            
            # Higher priority items should generally be scheduled earlier
            if current_priority >= next_priority:
                correct_orderings += 1
            elif current_priority == next_priority - 1:
                # Close priorities are acceptable
                correct_orderings += 0.7
        
        return correct_orderings / total_comparisons if total_comparisons > 0 else 1.0
    
    def _generate_feedback(self, conflict_score: float, deadline_score: float, 
                          efficiency_score: float, final_score: float) -> str:
        """Generate detailed feedback based on component scores."""
        feedback_parts = []
        
        # Overall assessment
        if final_score >= 0.9:
            feedback_parts.append("Excellent scheduling with optimal time management!")
        elif final_score >= 0.8:
            feedback_parts.append("Very good scheduling with minor optimization opportunities.")
        elif final_score >= 0.7:
            feedback_parts.append("Good scheduling but could be improved for better efficiency.")
        elif final_score >= 0.6:
            feedback_parts.append("Acceptable scheduling with several areas needing improvement.")
        else:
            feedback_parts.append("Poor scheduling quality requiring significant optimization.")
        
        # Component-specific feedback
        if conflict_score < 0.8:
            feedback_parts.append("Reduce scheduling conflicts by checking for overlapping events.")
        
        if deadline_score < 0.7:
            feedback_parts.append("Improve deadline management by scheduling tasks with appropriate buffers.")
        
        if efficiency_score < 0.7:
            feedback_parts.append("Optimize time usage by reducing gaps and using appropriate durations.")
        
        # Strengths
        best_component = max([
            ("conflict avoidance", conflict_score),
            ("deadline placement", deadline_score),
            ("time efficiency", efficiency_score)
        ], key=lambda x: x[1])
        
        if best_component[1] >= 0.8:
            feedback_parts.append(f"Strong performance in {best_component[0]}.")
        
        return " ".join(feedback_parts)
    
    def _create_empty_result(self, reason: str) -> Dict[str, Any]:
        """Create result for cases with no events to evaluate."""
        return {
            "score": 0.8,  # Neutral-positive score when no events to evaluate
            "feedback": f"Scheduling evaluation limited: {reason}",
            "details": {
                "error": reason,
                "component_scores": {
                    "conflict_avoidance": 0.8,
                    "deadline_placement": 0.8,
                    "time_efficiency": 0.8
                }
            },
            "timestamp": datetime.now().isoformat()
        }