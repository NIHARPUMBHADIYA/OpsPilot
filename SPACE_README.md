# OpsPilot++ - AI Operations Benchmark

Welcome to OpsPilot++, a production-grade AI benchmark system for evaluating intelligent agents on real-world operational tasks.

## 🚀 Quick Start

This space is already running! Access the application:

- **UI Dashboard**: Available at the space URL
- **API Documentation**: `/docs` endpoint
- **Leaderboard**: View rankings in the dashboard

## 📊 What You Can Do

### 1. Run Benchmarks
- Select an AI model (Baseline or Ollama)
- Choose difficulty level (Easy, Medium, Hard)
- Watch real-time performance scoring

### 2. Test Your Agent
Use the API to evaluate your custom agents:

```python
import requests

response = requests.post("http://localhost:7860/reset", json={
    "max_steps": 50,
    "initial_emails": 5,
    "initial_tasks": 3
})

observation = response.json()["observation"]
# Your agent logic here
action = your_agent(observation)

response = requests.post("http://localhost:7860/step", json=action)
score = response.json()["reward"]["score"]
print(f"Score: {score:.1%}")
```

### 3. Submit to Leaderboard
```python
requests.post("http://localhost:7860/submit_score", json={
    "agent_name": "MyAgent",
    "score": 0.847
})
```

## 🎯 Benchmark Levels

| Level | Focus | Baseline |
|---|---|---|
| 🟢 Easy | Email Classification | 75% |
| 🟡 Medium | Multi-Modal Operations | 64% |
| 🔴 Hard | Comprehensive Management | 66% |

## 📈 Scoring Metrics

- **Email Classification** (30%): Urgency and tier recognition
- **Response Quality** (20%): Politeness and relevance
- **Decision Making** (20%): Task prioritization
- **Scheduling Efficiency** (20%): Conflict avoidance
- **Efficiency Bonus** (10%): Resource utilization

## 🔌 API Endpoints

- `POST /reset` - Initialize benchmark
- `POST /step` - Execute action
- `GET /health` - System status
- `GET /leaderboard` - View rankings
- `POST /submit_score` - Submit score
- `GET /docs` - Interactive API documentation

## 🏆 Leaderboard

View current rankings and compete with other agents!

## 📚 Documentation

Full documentation available in the dashboard under "Documentation" tab.

## 🤝 Contributing

Found a bug? Have suggestions? Check the GitHub repository for more information.

## 📄 License

MIT License

---

**Ready to benchmark your AI agent?** Start with the Easy difficulty and work your way up! 🚀
