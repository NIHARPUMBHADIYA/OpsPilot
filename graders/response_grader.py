"""Deterministic response grader for OpsPilot - rule-based scoring with no randomness."""

import re
from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime


class ResponseGrader:
    """Deterministic grader for response quality using rule-based scoring."""
    
    def __init__(self) -> None:
        """Initialize response grader."""
        self.grader_type = "response"
        self.max_score = 1.0
        
        # Define politeness keywords
        self.politeness_keywords = {
            "apology": ["sorry", "apologize", "apologies", "regret"],
            "gratitude": ["thank you", "thanks", "grateful", "appreciate"],
            "assistance": ["assist", "help", "support", "serve", "aid"],
            "courtesy": ["please", "kindly", "would you", "could you", "may i"],
            "respect": ["understand", "respect", "value", "honor"]
        }
        
        # Define vague response indicators
        self.vague_indicators = [
            "something", "somehow", "somewhere", "someone", "sometime",
            "maybe", "perhaps", "might be", "could be", "possibly",
            "i think", "i believe", "i guess", "not sure", "unclear",
            "various", "several", "many", "some", "few", "certain",
            "general", "basic", "simple", "complex", "difficult"
        ]
        
        # Define hallucination indicators (overly specific claims without basis)
        self.hallucination_patterns = [
            r'\d{1,2}:\d{2}\s*(am|pm)',  # Specific times
            r'\$\d+\.\d{2}',  # Specific prices
            r'\d+\.\d+%',  # Specific percentages
            r'exactly \d+',  # Exact numbers
            r'precisely \d+',  # Precise numbers
            r'studies show that \d+',  # Fake study references
            r'research indicates \d+',  # Fake research claims
        ]
        
        # Define completeness indicators
        self.completeness_indicators = {
            "acknowledgment": ["received", "understand", "noted", "acknowledge"],
            "explanation": ["because", "due to", "reason", "caused by", "since"],
            "solution": ["will", "can", "solution", "resolve", "fix", "address"],
            "timeline": ["today", "tomorrow", "within", "by", "soon", "immediately"],
            "next_steps": ["next", "follow up", "contact", "update", "inform"]
        }
    
    def grade(self, response_text: str, email_text: str, 
              customer_tier: str = "free", urgency: int = 5) -> Dict[str, Any]:
        """
        Grade response quality using deterministic rule-based scoring.
        
        Args:
            response_text: The response to grade
            email_text: Original email text for relevance checking
            customer_tier: Customer tier (free, premium, vip)
            urgency: Email urgency level (1-10)
            
        Returns:
            Grading result with score between 0-1 and detailed breakdown
        """
        if not response_text or not response_text.strip():
            return self._create_empty_response_result("Empty response provided")
        
        # Clean and normalize text
        response_clean = response_text.strip()
        email_clean = email_text.strip() if email_text else ""
        
        # Grade each component
        relevance_score, relevance_details = self._grade_relevance(response_clean, email_clean)
        politeness_score, politeness_details = self._grade_politeness(response_clean, customer_tier)
        completeness_score, completeness_details = self._grade_completeness(response_clean, urgency)
        
        # Apply penalties
        hallucination_penalty, hallucination_details = self._calculate_hallucination_penalty(response_clean)
        vagueness_penalty, vagueness_details = self._calculate_vagueness_penalty(response_clean)
        
        # Calculate component scores (before penalties)
        component_scores = {
            "relevance": relevance_score,
            "politeness": politeness_score,
            "completeness": completeness_score
        }
        
        # Weighted combination (adjusted for better balance)
        base_score = (relevance_score * 0.35 + politeness_score * 0.25 + completeness_score * 0.4)
        
        # Apply penalties
        final_score = max(0.0, base_score - hallucination_penalty - vagueness_penalty)
        
        # Generate feedback
        feedback = self._generate_feedback(
            component_scores, hallucination_penalty, vagueness_penalty, final_score
        )
        
        return {
            "score": min(final_score, self.max_score),
            "feedback": feedback,
            "details": {
                "component_scores": component_scores,
                "base_score": base_score,
                "penalties": {
                    "hallucination": hallucination_penalty,
                    "vagueness": vagueness_penalty
                },
                "breakdown": {
                    "relevance": relevance_details,
                    "politeness": politeness_details,
                    "completeness": completeness_details,
                    "hallucination": hallucination_details,
                    "vagueness": vagueness_details
                },
                "response_length": len(response_clean.split()),
                "customer_tier": customer_tier,
                "urgency": urgency
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _grade_relevance(self, response_text: str, email_text: str) -> Tuple[float, Dict[str, Any]]:
        """Grade relevance to email intent using keyword overlap and topic matching."""
        if not email_text:
            return 0.5, {"reason": "No email text provided for comparison"}
        
        # Extract keywords from both texts
        email_keywords = self._extract_meaningful_keywords(email_text)
        response_keywords = self._extract_meaningful_keywords(response_text)
        
        if not email_keywords:
            return 0.5, {"reason": "No meaningful keywords in email"}
        
        # Calculate keyword overlap
        common_keywords = set(email_keywords) & set(response_keywords)
        keyword_overlap_ratio = len(common_keywords) / len(email_keywords)
        
        # Check for direct addressing of email intent
        intent_score = self._check_intent_addressing(email_text, response_text)
        
        # Check for topic consistency
        topic_score = self._check_topic_consistency(email_text, response_text)
        
        # Combine scores (more generous weighting)
        relevance_score = (keyword_overlap_ratio * 0.3 + intent_score * 0.5 + topic_score * 0.2)
        
        details = {
            "keyword_overlap_ratio": keyword_overlap_ratio,
            "common_keywords": list(common_keywords),
            "intent_score": intent_score,
            "topic_score": topic_score,
            "email_keywords_count": len(email_keywords),
            "response_keywords_count": len(response_keywords)
        }
        
        return min(relevance_score, 1.0), details
    
    def _grade_politeness(self, response_text: str, customer_tier: str) -> Tuple[float, Dict[str, Any]]:
        """Grade politeness using keyword detection and tone analysis."""
        response_lower = response_text.lower()
        
        # Count politeness keywords by category
        politeness_counts = {}
        total_politeness_score = 0.0
        
        for category, keywords in self.politeness_keywords.items():
            count = sum(1 for keyword in keywords if keyword in response_lower)
            politeness_counts[category] = count
            
            # Score each category (more generous scoring)
            if count > 0:
                category_score = min(count * 0.15, 0.25)  # Max 0.25 per category
                total_politeness_score += category_score
        
        # Bonus for customer tier appropriate politeness
        tier_bonus = self._calculate_tier_politeness_bonus(response_text, customer_tier)
        total_politeness_score += tier_bonus
        
        # Check for professional tone
        professional_score = self._check_professional_tone(response_text)
        total_politeness_score += professional_score
        
        # Penalty for impolite language
        impoliteness_penalty = self._calculate_impoliteness_penalty(response_text)
        total_politeness_score -= impoliteness_penalty
        
        details = {
            "politeness_counts": politeness_counts,
            "tier_bonus": tier_bonus,
            "professional_score": professional_score,
            "impoliteness_penalty": impoliteness_penalty,
            "total_keywords_found": sum(politeness_counts.values())
        }
        
        return max(0.0, min(total_politeness_score, 1.0)), details
    
    def _grade_completeness(self, response_text: str, urgency: int) -> Tuple[float, Dict[str, Any]]:
        """Grade completeness based on required elements and urgency level."""
        response_lower = response_text.lower()
        
        # Check for completeness indicators
        completeness_counts = {}
        total_completeness_score = 0.0
        
        for category, keywords in self.completeness_indicators.items():
            count = sum(1 for keyword in keywords if keyword in response_lower)
            completeness_counts[category] = count
            
            if count > 0:
                total_completeness_score += 0.15  # Each category worth 0.15
        
        # Length-based completeness (appropriate length)
        word_count = len(response_text.split())
        length_score = self._calculate_length_score(word_count, urgency)
        total_completeness_score += length_score
        
        # Structure score (paragraphs, sentences)
        structure_score = self._calculate_structure_score(response_text)
        total_completeness_score += structure_score
        
        # Urgency-appropriate completeness
        urgency_score = self._calculate_urgency_completeness(response_text, urgency)
        total_completeness_score += urgency_score
        
        details = {
            "completeness_counts": completeness_counts,
            "word_count": word_count,
            "length_score": length_score,
            "structure_score": structure_score,
            "urgency_score": urgency_score,
            "categories_covered": sum(1 for count in completeness_counts.values() if count > 0)
        }
        
        return min(total_completeness_score, 1.0), details
    
    def _calculate_hallucination_penalty(self, response_text: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate penalty for hallucinated content (overly specific claims)."""
        penalty = 0.0
        hallucination_matches = []
        
        # Check for hallucination patterns
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                hallucination_matches.extend(matches)
                penalty += len(matches) * 0.1  # 0.1 penalty per match
        
        # Check for unsupported specific claims
        specific_claim_patterns = [
            r'according to \w+',  # Fake attributions
            r'studies show',  # Unsupported study claims
            r'research proves',  # Unsupported research claims
            r'experts say',  # Vague expert claims
            r'\d+% of (customers|users|people)',  # Fake statistics
        ]
        
        for pattern in specific_claim_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                hallucination_matches.extend(matches)
                penalty += len(matches) * 0.15  # Higher penalty for fake claims
        
        details = {
            "hallucination_matches": hallucination_matches,
            "pattern_matches": len(hallucination_matches),
            "penalty_applied": penalty
        }
        
        return min(penalty, 0.5), details  # Cap penalty at 0.5
    
    def _calculate_vagueness_penalty(self, response_text: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate penalty for vague responses."""
        response_lower = response_text.lower()
        word_count = len(response_text.split())
        
        # Count vague indicators
        vague_count = sum(1 for indicator in self.vague_indicators 
                         if indicator in response_lower)
        
        # Calculate vagueness ratio
        vagueness_ratio = vague_count / word_count if word_count > 0 else 0
        
        # Apply penalty based on ratio
        if vagueness_ratio > 0.15:  # More than 15% vague words
            penalty = min(vagueness_ratio * 0.5, 0.3)  # Cap at 0.3
        elif vagueness_ratio > 0.10:  # More than 10% vague words
            penalty = vagueness_ratio * 0.3
        else:
            penalty = 0.0
        
        # Additional penalty for extremely short responses
        if word_count < 10:
            penalty += 0.2
        
        details = {
            "vague_indicators_found": vague_count,
            "vagueness_ratio": vagueness_ratio,
            "word_count": word_count,
            "penalty_applied": penalty
        }
        
        return penalty, details
    
    def _extract_meaningful_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords, excluding stop words."""
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "must", "shall", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they"
        }
        
        # Extract words, remove punctuation, filter stop words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _check_intent_addressing(self, email_text: str, response_text: str) -> float:
        """Check if response addresses the email's intent."""
        email_lower = email_text.lower()
        response_lower = response_text.lower()
        
        # Identify email intent patterns
        intent_patterns = {
            "question": ["?", "what", "how", "why", "when", "where", "who", "which"],
            "complaint": ["problem", "issue", "wrong", "error", "complaint", "dissatisfied"],
            "request": ["please", "can you", "could you", "would you", "need", "want"],
            "information": ["information", "details", "explain", "clarify", "understand"]
        }
        
        # Find email intent
        email_intent = None
        for intent, patterns in intent_patterns.items():
            if any(pattern in email_lower for pattern in patterns):
                email_intent = intent
                break
        
        if not email_intent:
            return 0.5  # Neutral score if intent unclear
        
        # Check if response addresses the intent
        response_patterns = {
            "question": ["answer", "because", "due to", "reason", "explanation"],
            "complaint": ["sorry", "apologize", "understand", "resolve", "fix"],
            "request": ["will", "can", "happy to", "certainly", "of course"],
            "information": ["here is", "the details", "to clarify", "explanation"]
        }
        
        if email_intent in response_patterns:
            addressing_patterns = response_patterns[email_intent]
            if any(pattern in response_lower for pattern in addressing_patterns):
                return 1.0
            else:
                return 0.3
        
        return 0.5
    
    def _check_topic_consistency(self, email_text: str, response_text: str) -> float:
        """Check if response stays on topic with the email."""
        email_keywords = set(self._extract_meaningful_keywords(email_text))
        response_keywords = set(self._extract_meaningful_keywords(response_text))
        
        if not email_keywords:
            return 0.5
        
        # Calculate topic overlap
        common_topics = email_keywords & response_keywords
        topic_consistency = len(common_topics) / len(email_keywords)
        
        return min(topic_consistency * 1.5, 1.0)  # Boost score slightly
    
    def _calculate_tier_politeness_bonus(self, response_text: str, customer_tier: str) -> float:
        """Calculate bonus for tier-appropriate politeness."""
        response_lower = response_text.lower()
        
        if customer_tier == "vip":
            # VIP customers should get extra polite treatment
            vip_indicators = ["valued", "important", "priority", "personally", "immediately"]
            vip_count = sum(1 for indicator in vip_indicators if indicator in response_lower)
            return min(vip_count * 0.05, 0.15)
        
        elif customer_tier == "premium":
            # Premium customers should get good treatment
            premium_indicators = ["appreciate", "thank you", "happy to help"]
            premium_count = sum(1 for indicator in premium_indicators if indicator in response_lower)
            return min(premium_count * 0.03, 0.1)
        
        return 0.0  # No bonus for free tier
    
    def _check_professional_tone(self, response_text: str) -> float:
        """Check for professional tone indicators."""
        response_lower = response_text.lower()
        
        professional_indicators = [
            "sincerely", "regards", "best", "professional", "business",
            "formal", "official", "appropriate", "proper"
        ]
        
        professional_count = sum(1 for indicator in professional_indicators 
                               if indicator in response_lower)
        
        return min(professional_count * 0.05, 0.1)
    
    def _calculate_impoliteness_penalty(self, response_text: str) -> float:
        """Calculate penalty for impolite language."""
        response_lower = response_text.lower()
        
        impolite_indicators = [
            "no", "can't", "won't", "impossible", "never", "absolutely not",
            "ridiculous", "stupid", "dumb", "wrong", "bad", "terrible"
        ]
        
        # Count impolite words
        impolite_count = sum(1 for indicator in impolite_indicators 
                           if indicator in response_lower)
        
        return min(impolite_count * 0.1, 0.3)  # Cap at 0.3
    
    def _calculate_length_score(self, word_count: int, urgency: int) -> float:
        """Calculate score based on appropriate response length."""
        if urgency >= 8:
            # High urgency: prefer concise responses
            if 20 <= word_count <= 80:
                return 0.15
            elif 10 <= word_count <= 120:
                return 0.1
            else:
                return 0.05
        else:
            # Normal urgency: prefer more detailed responses
            if 30 <= word_count <= 150:
                return 0.15
            elif 20 <= word_count <= 200:
                return 0.1
            else:
                return 0.05
    
    def _calculate_structure_score(self, response_text: str) -> float:
        """Calculate score based on response structure."""
        sentences = [s.strip() for s in response_text.split('.') if s.strip()]
        paragraphs = [p.strip() for p in response_text.split('\n') if p.strip()]
        
        score = 0.0
        
        # Sentence count
        if 2 <= len(sentences) <= 8:
            score += 0.05
        
        # Paragraph structure
        if len(paragraphs) > 1:
            score += 0.05
        
        return score
    
    def _calculate_urgency_completeness(self, response_text: str, urgency: int) -> float:
        """Calculate completeness score based on urgency level."""
        response_lower = response_text.lower()
        
        if urgency >= 8:
            # High urgency: should acknowledge urgency and provide immediate action
            urgency_indicators = ["urgent", "immediate", "asap", "priority", "right away"]
            action_indicators = ["will", "immediately", "now", "today", "escalate"]
            
            urgency_acknowledged = any(indicator in response_lower for indicator in urgency_indicators)
            action_provided = any(indicator in response_lower for indicator in action_indicators)
            
            score = 0.0
            if urgency_acknowledged:
                score += 0.1
            if action_provided:
                score += 0.1
            
            return score
        
        return 0.05  # Small bonus for normal urgency responses
    
    def _generate_feedback(self, component_scores: Dict[str, float], 
                          hallucination_penalty: float, vagueness_penalty: float,
                          final_score: float) -> str:
        """Generate detailed feedback based on scores and penalties."""
        feedback_parts = []
        
        # Overall assessment
        if final_score >= 0.9:
            feedback_parts.append("Excellent response quality!")
        elif final_score >= 0.8:
            feedback_parts.append("Very good response with minor areas for improvement.")
        elif final_score >= 0.7:
            feedback_parts.append("Good response but could be enhanced.")
        elif final_score >= 0.6:
            feedback_parts.append("Acceptable response with several improvement areas.")
        else:
            feedback_parts.append("Poor response quality requiring significant improvement.")
        
        # Component feedback
        if component_scores["relevance"] < 0.7:
            feedback_parts.append("Improve relevance to the original email content.")
        
        if component_scores["politeness"] < 0.7:
            feedback_parts.append("Enhance politeness with more courteous language.")
        
        if component_scores["completeness"] < 0.7:
            feedback_parts.append("Provide more complete responses with clear solutions.")
        
        # Penalty feedback
        if hallucination_penalty > 0.1:
            feedback_parts.append("Avoid making specific claims without supporting evidence.")
        
        if vagueness_penalty > 0.1:
            feedback_parts.append("Reduce vague language and provide more specific information.")
        
        # Strengths
        best_component = max(component_scores.items(), key=lambda x: x[1])
        if best_component[1] >= 0.8:
            feedback_parts.append(f"Strong performance in {best_component[0]}.")
        
        return " ".join(feedback_parts)
    
    def _create_empty_response_result(self, reason: str) -> Dict[str, Any]:
        """Create result for empty or invalid responses."""
        return {
            "score": 0.0,
            "feedback": f"Response grading failed: {reason}",
            "details": {
                "error": reason,
                "component_scores": {"relevance": 0.0, "politeness": 0.0, "completeness": 0.0},
                "penalties": {"hallucination": 0.0, "vagueness": 0.0}
            },
            "timestamp": datetime.now().isoformat()
        }