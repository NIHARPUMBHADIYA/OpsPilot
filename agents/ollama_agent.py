"""
Ollama-based agent for OpsPilot++
Uses local Ollama models for zero-cost, privacy-preserving AI operations.
"""

import json
import requests
from typing import Dict, Any, Optional
import time

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "llama2"  # Fallback model
OLLAMA_RECOMMENDED_MODELS = [
    "llama2",           # Fast, good quality
    "mistral",          # Faster, decent quality
    "neural-chat",      # Optimized for chat
    "dolphin-mixtral",  # High quality
    "openchat",         # Fast and capable
]

def check_ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_available_models() -> list:
    """Get list of available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"].split(":")[0] for m in data.get("models", [])]
            return list(set(models))  # Remove duplicates
        return []
    except:
        return []

def build_ollama_prompt(observation: Dict[str, Any]) -> str:
    """Build a concise prompt for Ollama models."""
    emails = observation.get("emails", [])
    tasks = observation.get("tasks", [])
    
    # Build email summary
    email_summary = ""
    if emails:
        for i, email in enumerate(emails[:3], 1):  # First 3 emails
            email_summary += f"\nEmail {i}: {email.get('text', '')[:100]} (Urgency: {email.get('urgency', 5)}/10)"
    
    # Build task summary
    task_summary = ""
    if tasks:
        for i, task in enumerate(tasks[:3], 1):  # First 3 tasks
            task_summary += f"\nTask {i}: {task.get('description', '')[:100]} (Deadline: {task.get('deadline', 0)}min)"
    
    prompt = f"""You are an AI operations manager. Analyze this situation and provide a JSON action plan.

EMAILS:{email_summary or "None"}

TASKS:{task_summary or "None"}

Time remaining: {observation.get('time_remaining', 480)} minutes
Energy budget: {observation.get('energy_budget', 100)}%

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "email_actions": [
    {{"email_id": "e1", "action_type": "respond", "priority": 8, "response_content": "Thank you for reaching out. I will prioritize this."}}
  ],
  "task_priorities": [
    {{"task_id": "t1", "priority_level": 8, "reasoning": "High urgency deadline"}}
  ],
  "scheduling": [],
  "skip_ids": []
}}"""
    
    return prompt

def call_ollama(model: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
    """Call Ollama API to generate response."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            return None
            
    except requests.exceptions.Timeout:
        return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from Ollama response."""
    try:
        # Try direct JSON parse
        return json.loads(response)
    except:
        pass
    
    try:
        # Try to find JSON in response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except:
        pass
    
    return None

def validate_and_fix_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and fix action structure."""
    # Ensure required keys exist
    if "email_actions" not in action:
        action["email_actions"] = []
    if "task_priorities" not in action:
        action["task_priorities"] = []
    if "scheduling" not in action:
        action["scheduling"] = []
    if "skip_ids" not in action:
        action["skip_ids"] = []
    
    # Validate email_actions
    for ea in action.get("email_actions", []):
        if "action_type" not in ea:
            ea["action_type"] = "respond"
        if "priority" not in ea:
            ea["priority"] = 5
        else:
            try:
                ea["priority"] = max(1, min(10, int(ea["priority"])))
            except:
                ea["priority"] = 5
        if "response_content" not in ea:
            ea["response_content"] = "Thank you for your message."
    
    # Validate task_priorities
    for tp in action.get("task_priorities", []):
        if "priority_level" not in tp:
            tp["priority_level"] = 5
        else:
            try:
                tp["priority_level"] = max(1, min(10, int(tp["priority_level"])))
            except:
                tp["priority_level"] = 5
        if "reasoning" not in tp:
            tp["reasoning"] = "Standard priority"
    
    return action

class OllamaAgent:
    """Ollama-based agent for OpsPilot operations."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize Ollama agent."""
        self.available = check_ollama_available()
        
        if not self.available:
            raise RuntimeError(
                "Ollama is not running. Please start Ollama with:\n"
                "  ollama serve\n"
                "Then pull a model:\n"
                "  ollama pull llama2"
            )
        
        # Get available models
        available_models = get_available_models()
        
        if model and model in available_models:
            self.model = model
        elif available_models:
            # Use first available model
            self.model = available_models[0]
        else:
            raise RuntimeError(
                "No Ollama models found. Please pull a model:\n"
                "  ollama pull llama2"
            )
        
        self.agent_id = f"ollama_agent_{self.model}"
        self.action_count = 0
        self.start_time = time.time()
    
    def execute_action(self, action_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action using Ollama."""
        if action_type != "generate_action":
            return {
                "success": False,
                "error": f"Unknown action type: {action_type}"
            }
        
        observation = context.get("observation", {})
        
        try:
            # Build prompt
            prompt = build_ollama_prompt(observation)
            
            # Call Ollama
            response = call_ollama(self.model, prompt)
            
            if not response:
                return {
                    "success": False,
                    "error": "Ollama did not return a response"
                }
            
            # Extract JSON
            action = extract_json_from_response(response)
            
            if not action:
                return {
                    "success": False,
                    "error": "Could not parse JSON from Ollama response"
                }
            
            # Validate and fix
            action = validate_and_fix_action(action)
            
            self.action_count += 1
            
            return {
                "success": True,
                "result": action,
                "reasoning": f"Generated by Ollama model: {self.model}",
                "confidence": 0.75,
                "execution_time": time.time() - self.start_time,
                "model": self.model
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "model": self.model,
            "available": self.available,
            "action_count": self.action_count,
            "uptime": time.time() - self.start_time
        }
