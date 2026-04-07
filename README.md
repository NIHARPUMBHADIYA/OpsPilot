# OpsPilot++

## 🚀 AI Operations Benchmark System

**Production-Grade Evaluation Platform for Intelligent Agents**

Repository: https://github.com/NIHARPUMBHADIYA/OpsPilot-.git

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb?style=flat-square&logo=react)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**[Quick Start](#quick-start) • [Features](#features) • [API](#api-reference) • [Leaderboard](#leaderboard) • [Docs](#documentation)**

---

## 📋 Overview

**OpsPilot++** is a comprehensive AI benchmark system that evaluates intelligent agents on real-world employee-level operational tasks. It provides standardized evaluation protocols, multi-dimensional scoring, and competitive leaderboards for benchmarking AI agent performance.

### What Makes This Different

| Traditional Benchmarks | OpsPilot++ |
|---|---|
| Single objective | Multi-objective optimization |
| Immediate feedback | Delayed consequences |
| Perfect information | Partial/noisy information |
| Isolated tasks | Integrated operations |
| Simple scoring | Advanced multi-dimensional evaluation |

---

## ⚡ Quick Start

### Prerequisites

```
✓ Python 3.10+
✓ Node.js 18+
✓ Ollama (optional)
```

### Installation & Run

```bash
# Clone repository
git clone https://github.com/NIHARPUMBHADIYA/OpsPilot-.git
cd OpsPilot

# Start everything
python main.py
```

**That's it!** The system will automatically:
- Install all dependencies
- Start backend API (port 7860)
- Start frontend UI (port 3000)
- Check for Ollama support

### Access

| Component | URL |
|---|---|
| **UI Dashboard** | http://localhost:3000 |
| **API** | http://localhost:7860 |
| **API Docs** | http://localhost:7860/docs |

---

## ✨ Features

### 🎯 Core Capabilities

**Benchmark Runner**
- Real-time agent execution
- Live performance scoring
- Multi-model support
- Progressive difficulty levels

**Leaderboard System**
- Competitive rankings
- Performance tracking
- Statistical analysis
- Historical data

**Advanced Evaluation**
- Counterfactual analysis
- Explainability tools
- Multi-agent coordination
- Adversarial testing

**Developer Tools**
- REST API
- Interactive documentation
- Python SDK
- Example agents

### 📊 Evaluation Metrics

```
Email Classification      30%
Response Quality          20%
Decision Making           20%
Scheduling Efficiency     20%
Efficiency Bonus          10%
```

### 🎮 Task Levels

| Level | Focus | Complexity | Baseline |
|---|---|---|---|
| 🟢 Easy | Email Classification | Basic | 75% |
| 🟡 Medium | Multi-Modal Operations | Intermediate | 64% |
| 🔴 Hard | Comprehensive Management | Advanced | 66% |

---

## 🏗️ Architecture

### Backend Stack

- **Framework**: FastAPI
- **Environment**: Custom operational simulation
- **Graders**: Multi-dimensional evaluation system
- **Baseline**: Rule-based reference agent (65.9%)

### Frontend Stack

- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **State**: Zustand
- **HTTP**: Axios

### System Flow

```
User Interface (React)
        ↓
    API Gateway (FastAPI)
        ↓
Environment Simulation
        ↓
Multi-Dimensional Graders
        ↓
Reward & Feedback
```

---

## 🔌 API Reference

### Core Endpoints

#### Initialize Benchmark
```bash
POST /reset
Content-Type: application/json

{
  "max_steps": 50,
  "initial_emails": 5,
  "initial_tasks": 3,
  "random_seed": 42
}
```

#### Execute Action
```bash
POST /step
Content-Type: application/json

{
  "email_actions": [...],
  "task_priorities": [...],
  "scheduling": [...],
  "skip_ids": [...]
}
```

#### Get Leaderboard
```bash
GET /leaderboard
```

#### Submit Score
```bash
POST /submit_score
Content-Type: application/json

{
  "agent_name": "MyAgent",
  "score": 0.847
}
```

### Advanced Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | System status |
| `GET /models` | Available models |
| `POST /counterfactual` | Alternative evaluation |
| `GET /explain` | Decision explanations |
| `GET /adversarial-analysis` | Robustness testing |

**Full API Documentation**: http://localhost:7860/docs

---

## 💡 Usage Examples

### Simple Agent

```python
import requests

# Initialize
response = requests.post("http://localhost:7860/reset", json={
    "max_steps": 50,
    "initial_emails": 5,
    "initial_tasks": 3
})
observation = response.json()["observation"]

# Your agent logic
def my_agent(obs):
    emails = sorted(obs["emails"], 
                   key=lambda x: x["urgency"], 
                   reverse=True)
    
    return {
        "email_actions": [
            {"email_id": e["id"], "action_type": "reply"}
            for e in emails[:3]
        ],
        "task_priorities": [],
        "scheduling": [],
        "skip_ids": []
    }

# Execute
action = my_agent(observation)
response = requests.post("http://localhost:7860/step", json=action)
score = response.json()["reward"]["score"]

print(f"Score: {score:.1%}")
```

### LLM-Based Agent

```python
def llm_agent(observation):
    # Use Ollama for intelligent decisions
    prompt = format_observation(observation)
    response = ollama.generate(prompt)
    action = parse_action(response)
    return action
```

---

## 🏆 Leaderboard

### Current Top Performers

| Rank | Agent | Score | Model |
|---|---|---|---|
| 🥇 | Your Agent | -- | -- |
| 🥈 | Baseline | 65.9% | Rule-Based |
| 🥉 | -- | -- | -- |

**View Full Leaderboard**: http://localhost:3000/leaderboard

---

## 🎯 Hackathon Guide

### Getting Started

1. **Understand the Task**
   - Read the documentation
   - Review baseline implementation
   - Test with Easy difficulty

2. **Build Your Agent**
   - Start simple (rule-based)
   - Iterate and improve
   - Test on all difficulties

3. **Optimize Performance**
   - Use explainability tools
   - Analyze failures
   - Refine strategy

4. **Submit & Compete**
   - Submit to leaderboard
   - Track rankings
   - Iterate for better scores

### Pro Tips

**Do This ✅**
- Start with Easy difficulty
- Use the explainability endpoint
- Test incrementally
- Monitor the leaderboard
- Document your approach

**Avoid This ❌**
- Ignoring VIP customers (-0.30)
- Creating scheduling conflicts (-0.15)
- Hallucinating information (-0.20)
- Missing deadlines (-0.25)
- Poor prioritization (-0.10)

---

## 🛠️ Deployment Options

### Option 1: Full Stack (Recommended)
```bash
python main.py
```

### Option 2: Backend Only
```bash
python main.py --backend-only
```

### Option 3: Custom Port
```bash
python main.py --port 8000
```

### Option 4: Development Mode
```bash
# Terminal 1: Backend
python main.py --backend-only

# Terminal 2: Frontend
cd ui && npm run dev
```

---

## 📚 Documentation

### In-App Resources

| Resource | Location |
|---|---|
| **Getting Started** | UI → Documentation |
| **API Reference** | http://localhost:7860/docs |
| **Scoring Details** | UI → Documentation → Scoring System |
| **Task Specifications** | UI → Documentation → Task Types |

### Code Documentation

- `main.py` - Entry point and configuration
- `env/environment.py` - Environment implementation
- `graders/` - Evaluation graders
- `baseline/agent.py` - Reference implementation
- `ui/src/` - Frontend components

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
python main.py --port 8000
```

### Ollama Not Found
```bash
# Install Ollama
# Windows: winget install ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

ollama serve
```

### UI Not Loading
```bash
# Verify backend
curl http://localhost:7860/health

# Rebuild UI
cd ui && npm install && npm run build
```

### API Connection Error
```bash
# Check logs
python main.py --backend-only

# Verify endpoint
curl http://localhost:7860/docs
```

---

## 📊 Performance Baseline

### Rule-Based Baseline (65.9%)

| Metric | Score |
|---|---|
| Email Classification | 75.0% |
| Response Quality | 64.0% |
| Decision Making | 100.0% |
| Scheduling | 100.0% |
| Overall | 65.9% |

**Your Goal**: Beat the baseline! 🎯

---

## 🤝 Contributing

We welcome contributions! Areas for enhancement:

- New grader implementations
- Advanced baseline agents
- Task variants
- UI improvements
- Documentation

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🔗 Citation

```bibtex
@misc{opspilot2024,
  title={OpsPilot++: AI Operations Benchmark},
  author={OpsPilot Team},
  year={2024}
}
```

---

## 🚀 Ready to Benchmark?

```bash
python main.py
```

Then open → **http://localhost:3000**

---

**Questions?** Check the [Documentation](http://localhost:3000/documentation)

**Want to compete?** Visit the [Leaderboard](http://localhost:3000/leaderboard)

**Ready to build?** Start the [Benchmark Runner](http://localhost:3000/benchmark)

---

Made with ❤️ for the AI Community
