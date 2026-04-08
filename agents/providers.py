"""
Universal AI provider system for OpsPilot++ benchmarking.
Supports any AI model — from tiny local models to massive frontier models.
"""

import json
import requests
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Simple in-memory cache for API responses
_RESPONSE_CACHE: Dict[str, tuple[str, float]] = {}
_CACHE_TTL = 86400  # 24 hour cache (very aggressive)
_LAST_REQUEST_TIME = {}  # Track last request time per provider
_MIN_REQUEST_INTERVAL = 2.0  # Minimum 2 seconds between requests

# ---------------------------------------------------------------------------
# Provider registry — add new providers here
# ---------------------------------------------------------------------------
PROVIDERS = {
    # ── OpenAI ──────────────────────────────────────────────────────────────
    "openai": {
        "label": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "needs_key": True,
        "base_url": None,
    },
    # ── Anthropic ───────────────────────────────────────────────────────────
    "anthropic": {
        "label": "Anthropic (Claude)",
        "models": [
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        "needs_key": True,
        "base_url": None,
    },
    # ── Google Gemini ────────────────────────────────────────────────────────
    "google": {
        "label": "Google (Gemini)",
        "models": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
        ],
        "needs_key": True,
        "base_url": None,
    },
    # ── Mistral ──────────────────────────────────────────────────────────────
    "mistral": {
        "label": "Mistral AI",
        "models": [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-7b",
            "open-mixtral-8x7b",
            "open-mixtral-8x22b",
        ],
        "needs_key": True,
        "base_url": "https://api.mistral.ai/v1",
    },
    # ── Cohere ───────────────────────────────────────────────────────────────
    "cohere": {
        "label": "Cohere",
        "models": ["command-r-plus", "command-r", "command", "command-light"],
        "needs_key": True,
        "base_url": None,
    },
    # ── Groq (fast inference) ────────────────────────────────────────────────
    "groq": {
        "label": "Groq",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "gemma-7b-it",
        ],
        "needs_key": True,
        "base_url": "https://api.groq.com/openai/v1",
    },
    # ── Together AI ──────────────────────────────────────────────────────────
    "together": {
        "label": "Together AI",
        "models": [
            "meta-llama/Llama-3-70b-chat-hf",
            "meta-llama/Llama-3-8b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "google/gemma-2-27b-it",
            "Qwen/Qwen2-72B-Instruct",
        ],
        "needs_key": True,
        "base_url": "https://api.together.xyz/v1",
    },
    # ── Ollama (local models) ────────────────────────────────────────────────
    "ollama": {
        "label": "Ollama (Local)",
        "models": [
            "llama3.2", "llama3.1", "llama3",
            "mistral", "mixtral",
            "gemma2", "gemma",
            "phi3", "phi",
            "qwen2.5", "qwen2",
            "deepseek-r1", "deepseek-coder",
            "codellama", "vicuna",
            "neural-chat", "starling-lm",
            "tinyllama",
        ],
        "needs_key": False,
        "base_url": "http://localhost:11434/v1",
    },
    # ── Custom / Any OpenAI-compatible endpoint ───────────────────────────────
    "custom": {
        "label": "Custom Endpoint (OpenAI-compatible)",
        "models": [],          # user types the model name
        "needs_key": False,    # optional
        "base_url": None,      # user provides URL
    },
    # ── Baseline (local rule-based) ───────────────────────────────────────────
    "baseline": {
        "label": "Baseline Agent (built-in)",
        "models": ["baseline"],
        "needs_key": False,
        "base_url": None,
    },
}


# ---------------------------------------------------------------------------
# Shared prompt builder
# ---------------------------------------------------------------------------
def build_prompt(observation: Dict[str, Any]) -> str:
    """Build ultra-minimal prompt - ~30 tokens only."""
    emails = observation.get("emails", [])
    tasks = observation.get("tasks", [])
    
    # Absolute minimum - just IDs and urgency
    e_str = ",".join([f"{e.get('id','?')}:{e.get('urgency',0)}" for e in emails[:1]])
    t_str = ",".join([f"{t.get('task_id','?')}:{t.get('deadline',0)}" for t in tasks[:1]])
    
    return f"""E:{e_str} T:{t_str}
{{"email_actions":[{{"email_id":"e1","action_type":"respond","priority":5,"response_content":"OK"}}],"task_priorities":[{{"task_id":"t1","priority_level":5,"reasoning":"std"}}],"scheduling":[],"skip_ids":[]}}"""


# ---------------------------------------------------------------------------
# Individual provider callers
# ---------------------------------------------------------------------------

def _call_openai_compatible(base_url: Optional[str], api_key: str, model: str, prompt: str) -> str:
    """Generic caller for any OpenAI-compatible API (OpenAI, Groq, Together, Mistral, Ollama, custom)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")

    kwargs = {"api_key": api_key or "ollama"}
    if base_url:
        kwargs["base_url"] = base_url

    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def _call_google(api_key: str, model: str, prompt: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")

    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model)
    response = m.generate_content(prompt)
    return response.text.strip()


def _call_cohere(api_key: str, model: str, prompt: str) -> str:
    try:
        import cohere
    except ImportError:
        raise RuntimeError("cohere package not installed. Run: pip install cohere")

    co = cohere.Client(api_key)
    response = co.chat(model=model, message=prompt)
    return response.text.strip()


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def _validate_action(action: Dict[str, Any]) -> tuple[bool, str]:
    """Validate action format and fix common issues."""
    try:
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
            if ea["action_type"] not in ["respond", "skip", "delegate"]:
                ea["action_type"] = "respond"
            if "priority" not in ea:
                ea["priority"] = 5
            else:
                try:
                    ea["priority"] = int(ea["priority"]) if isinstance(ea["priority"], str) else ea["priority"]
                    ea["priority"] = max(1, min(10, ea["priority"]))
                except (ValueError, TypeError):
                    ea["priority"] = 5
            if "response_content" not in ea:
                ea["response_content"] = "Thank you for your message."
        
        # Validate task_priorities
        for tp in action.get("task_priorities", []):
            if "priority_level" not in tp:
                tp["priority_level"] = 5
            else:
                try:
                    tp["priority_level"] = int(tp["priority_level"]) if isinstance(tp["priority_level"], str) else tp["priority_level"]
                    tp["priority_level"] = max(1, min(10, tp["priority_level"]))
                except (ValueError, TypeError):
                    tp["priority_level"] = 5
            if "reasoning" not in tp:
                tp["reasoning"] = "Standard priority"
        
        # Validate scheduling
        for sched in action.get("scheduling", []):
            if "scheduled_time" not in sched:
                sched["scheduled_time"] = 0
            else:
                try:
                    sched["scheduled_time"] = int(sched["scheduled_time"])
                except (ValueError, TypeError):
                    sched["scheduled_time"] = 0
            if "duration" not in sched:
                sched["duration"] = 30
            else:
                try:
                    sched["duration"] = int(sched["duration"])
                except (ValueError, TypeError):
                    sched["duration"] = 30
        
        return True, ""
    except Exception as e:
        return False, str(e)


def get_agent(
    provider: str,
    model: str,
    api_key: str,
    observation: Dict[str, Any],
    custom_base_url: str = "",
) -> Dict[str, Any]:
    """
    Optimized agent call with aggressive caching and fallbacks.
    Priority: Cache > Ollama (FREE) > Baseline (FREE) > API (if key provided)
    
    Users without premium API keys can use Ollama or Baseline for FREE!
    """
    cache_key = hashlib.md5(json.dumps(observation, sort_keys=True).encode()).hexdigest()
    
    # 1. CHECK CACHE FIRST (instant response, no API call)
    if cache_key in _RESPONSE_CACHE:
        cached_response, cache_time = _RESPONSE_CACHE[cache_key]
        if time.time() - cache_time < _CACHE_TTL:
            try:
                action = json.loads(cached_response)
                return {"success": True, "action": action, "raw_response": cached_response, 
                        "provider": "cache", "model": "cached", "error": None}
            except:
                pass
    
    # 2. TRY OLLAMA FIRST (FREE, local, no API key needed)
    # Only skip if user explicitly selected a different provider
    if provider not in ("baseline", "openai", "anthropic", "google", "mistral", "cohere", "groq", "together", "custom"):
        try:
            from agents.ollama_agent import OllamaAgent, check_ollama_available
            if check_ollama_available():
                try:
                    agent = OllamaAgent()
                    result = agent.execute_action("generate_action", {"observation": observation})
                    if result and result.get("success") and "result" in result:
                        action = result["result"]
                        _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                        return {"success": True, "action": action, "raw_response": json.dumps(action), 
                                "provider": "ollama", "model": agent.model, "error": None}
                except:
                    pass  # Fall through to baseline
        except:
            pass  # Ollama module not available
    
    # 3. USE BASELINE AGENT (FREE, always works, no API key needed)
    # Use if: provider is "baseline" OR no API key provided AND not explicitly requesting API
    if provider == "baseline" or (not api_key and provider not in ("openai", "anthropic", "google", "mistral", "cohere", "groq", "together", "custom")):
        try:
            from baseline.agent import BaselineAgent
            agent = BaselineAgent()
            result = agent.execute_action("generate_action", {"observation": observation})
            if result and "action" in result:
                action = result["action"]
                _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                return {"success": True, "action": action, "raw_response": json.dumps(action), 
                        "provider": "baseline", "model": "baseline", "error": None}
        except Exception as e:
            pass  # Fall through to API if baseline fails
    
    # 4. RATE LIMITING (before API calls)
    if provider in _LAST_REQUEST_TIME:
        elapsed = time.time() - _LAST_REQUEST_TIME[provider]
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _LAST_REQUEST_TIME[provider] = time.time()
    
    # 5. CALL API (only if user explicitly provided API key and requested specific provider)
    prompt = build_prompt(observation)
    raw = ""

    try:
        if provider == "baseline":
            raise ValueError("Use baseline path")
        elif provider == "ollama":
            # Explicit Ollama request
            from agents.ollama_agent import OllamaAgent
            agent = OllamaAgent(model)
            result = agent.execute_action("generate_action", {"observation": observation})
            if result and result.get("success"):
                action = result["result"]
                _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                return {"success": True, "action": action, "raw_response": json.dumps(action), 
                        "provider": "ollama", "model": model, "error": None}
            else:
                raise ValueError(result.get("error", "Ollama failed"))
        elif provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required")
            raw = _call_openai_compatible(None, api_key, model, prompt)
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key required")
            raw = _call_anthropic(api_key, model, prompt)
        elif provider == "google":
            if not api_key:
                raise ValueError("Google API key required")
            raw = _call_google(api_key, model, prompt)
        elif provider == "cohere":
            if not api_key:
                raise ValueError("Cohere API key required")
            raw = _call_cohere(api_key, model, prompt)
        elif provider in ("mistral", "groq", "together"):
            if not api_key:
                raise ValueError(f"{provider.title()} API key required")
            base_url = PROVIDERS[provider]["base_url"]
            raw = _call_openai_compatible(base_url, api_key, model, prompt)
        elif provider == "custom":
            if not custom_base_url:
                raise ValueError("Custom provider requires base URL")
            raw = _call_openai_compatible(custom_base_url.rstrip("/"), api_key or "custom", model, prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Parse response
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        action = json.loads(clean)
        is_valid, _ = _validate_action(action)
        
        if is_valid:
            _RESPONSE_CACHE[cache_key] = (clean, time.time())
            return {"success": True, "action": action, "raw_response": raw, 
                    "provider": provider, "model": model, "error": None}
        else:
            # Validation failed - try Ollama, then baseline
            try:
                from agents.ollama_agent import OllamaAgent, check_ollama_available
                if check_ollama_available():
                    try:
                        agent = OllamaAgent()
                        result = agent.execute_action("generate_action", {"observation": observation})
                        if result and result.get("success") and "result" in result:
                            action = result["result"]
                            _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                            return {"success": True, "action": action, "raw_response": json.dumps(action), 
                                    "provider": "ollama", "model": agent.model, "error": None}
                    except:
                        pass
            except:
                pass
            
            # Fallback to baseline
            from baseline.agent import BaselineAgent
            agent = BaselineAgent()
            result = agent.execute_action("generate_action", {"observation": observation})
            if result and "action" in result:
                action = result["action"]
                _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                return {"success": True, "action": action, "raw_response": json.dumps(action), 
                        "provider": "baseline", "model": "baseline", "error": None}

    except json.JSONDecodeError as e:
        # JSON parse failed - try Ollama, then baseline
        try:
            from agents.ollama_agent import OllamaAgent, check_ollama_available
            if check_ollama_available():
                try:
                    agent = OllamaAgent()
                    result = agent.execute_action("generate_action", {"observation": observation})
                    if result and result.get("success") and "result" in result:
                        action = result["result"]
                        _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                        return {"success": True, "action": action, "raw_response": json.dumps(action), 
                                "provider": "ollama", "model": agent.model, "error": None}
                except:
                    pass
        except:
            pass
        
        # Fallback to baseline
        try:
            from baseline.agent import BaselineAgent
            agent = BaselineAgent()
            result = agent.execute_action("generate_action", {"observation": observation})
            if result and "action" in result:
                action = result["action"]
                _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                return {"success": True, "action": action, "raw_response": json.dumps(action), 
                        "provider": "baseline", "model": "baseline", "error": None}
        except:
            pass
        return {"success": False, "action": {}, "raw_response": raw, "provider": provider, 
                "model": model, "error": f"JSON parse failed: {str(e)[:100]}"}
    except Exception as e:
        # API call failed - try Ollama, then baseline
        try:
            from agents.ollama_agent import OllamaAgent, check_ollama_available
            if check_ollama_available():
                try:
                    agent = OllamaAgent()
                    result = agent.execute_action("generate_action", {"observation": observation})
                    if result and result.get("success") and "result" in result:
                        action = result["result"]
                        _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                        return {"success": True, "action": action, "raw_response": json.dumps(action), 
                                "provider": "ollama", "model": agent.model, "error": None}
                except:
                    pass
        except:
            pass
        
        # Fallback to baseline
        try:
            from baseline.agent import BaselineAgent
            agent = BaselineAgent()
            result = agent.execute_action("generate_action", {"observation": observation})
            if result and "action" in result:
                action = result["action"]
                _RESPONSE_CACHE[cache_key] = (json.dumps(action), time.time())
                return {"success": True, "action": action, "raw_response": json.dumps(action), 
                        "provider": "baseline", "model": "baseline", "error": None}
        except:
            pass
        return {"success": False, "action": {}, "raw_response": raw, "provider": provider, 
                "model": model, "error": str(e)[:100]}
