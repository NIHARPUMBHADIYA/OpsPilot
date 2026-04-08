"""
Inference module for OpsPilot++ benchmark system.
This module provides the main inference interface for the hackathon.
"""

import requests
import json
from typing import Dict, Any, Optional, List
from enum import Enum

# Configuration
API_BASE_URL = "http://localhost:7860"
DEFAULT_TIMEOUT = 30

class TaskDifficulty(Enum):
    """Task difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class AgentType(Enum):
    """Available agent types"""
    BASELINE = "baseline"
    OLLAMA = "ollama"

class OpsPilotInference:
    """Main inference class for OpsPilot++ benchmark"""
    
    def __init__(self, api_url: str = API_BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the inference client.
        
        Args:
            api_url: Base URL of the API
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.timeout = timeout
        self.session_id = None
        self.current_task = None
        self.current_difficulty = None
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def reset(self) -> Dict[str, Any]:
        """Reset the environment"""
        try:
            response = requests.post(
                f"{self.api_url}/reset",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data.get("session_id")
            return data
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_available_tasks(self) -> Dict[str, Any]:
        """Get available tasks"""
        try:
            response = requests.get(
                f"{self.api_url}/tasks",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get available models"""
        try:
            response = requests.get(
                f"{self.api_url}/models",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def step(self, action: str, model: str = "baseline") -> Dict[str, Any]:
        """
        Execute a step in the environment.
        
        Args:
            action: The action to execute
            model: The model to use (baseline or ollama)
        
        Returns:
            Response from the API
        """
        try:
            payload = {
                "action": action,
                "model": model
            }
            response = requests.post(
                f"{self.api_url}/step",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        try:
            response = requests.get(
                f"{self.api_url}/state",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def submit_score(self, agent_name: str, score: float, task: str, difficulty: str, model: str) -> Dict[str, Any]:
        """
        Submit a score to the leaderboard.
        
        Args:
            agent_name: Name of the agent
            score: Score achieved (0-100)
            task: Task name
            difficulty: Difficulty level
            model: Model used
        
        Returns:
            Response from the API
        """
        try:
            payload = {
                "agent_name": agent_name,
                "score": score,
                "task": task,
                "difficulty": difficulty,
                "model": model
            }
            response = requests.post(
                f"{self.api_url}/submit_score",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
        """Get the leaderboard"""
        try:
            response = requests.get(
                f"{self.api_url}/leaderboard?limit={limit}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def run_benchmark(self, task: str, difficulty: str, model: str = "baseline", max_steps: int = 10) -> Dict[str, Any]:
        """
        Run a complete benchmark.
        
        Args:
            task: Task to run
            difficulty: Difficulty level
            model: Model to use
            max_steps: Maximum number of steps
        
        Returns:
            Benchmark results
        """
        try:
            # Reset environment
            reset_result = self.reset()
            if "error" in reset_result:
                return reset_result
            
            # Run steps
            steps_results = []
            for i in range(max_steps):
                step_result = self.step(f"step_{i}", model)
                steps_results.append(step_result)
                
                if step_result.get("done"):
                    break
            
            return {
                "status": "success",
                "task": task,
                "difficulty": difficulty,
                "model": model,
                "steps": len(steps_results),
                "results": steps_results
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Convenience functions
def create_client(api_url: str = API_BASE_URL) -> OpsPilotInference:
    """Create an inference client"""
    return OpsPilotInference(api_url)

def health_check(api_url: str = API_BASE_URL) -> bool:
    """Quick health check"""
    client = OpsPilotInference(api_url)
    result = client.health_check()
    return result.get("status") == "healthy"

def reset_environment(api_url: str = API_BASE_URL) -> Dict[str, Any]:
    """Reset the environment"""
    client = OpsPilotInference(api_url)
    return client.reset()

def get_available_tasks(api_url: str = API_BASE_URL) -> Dict[str, Any]:
    """Get available tasks"""
    client = OpsPilotInference(api_url)
    return client.get_available_tasks()

def get_available_models(api_url: str = API_BASE_URL) -> Dict[str, Any]:
    """Get available models"""
    client = OpsPilotInference(api_url)
    return client.get_available_models()


if __name__ == "__main__":
    # Example usage
    print("OpsPilot++ Inference Module")
    print("=" * 50)
    
    client = create_client()
    
    # Health check
    print("\n1. Health Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # Get available tasks
    print("\n2. Available Tasks:")
    tasks = client.get_available_tasks()
    print(json.dumps(tasks, indent=2))
    
    # Get available models
    print("\n3. Available Models:")
    models = client.get_available_models()
    print(json.dumps(models, indent=2))
    
    # Reset environment
    print("\n4. Reset Environment:")
    reset = client.reset()
    print(json.dumps(reset, indent=2))
    
    # Get leaderboard
    print("\n5. Leaderboard:")
    leaderboard = client.get_leaderboard()
    print(json.dumps(leaderboard, indent=2))
