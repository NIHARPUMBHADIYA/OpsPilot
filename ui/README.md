# OpsPilot++ Benchmark UI

Modern, beautifully designed React-based interface for the OpsPilot++ AI Operations Benchmark system.

## What is OpsPilot++?

OpsPilot++ is a comprehensive AI benchmark that evaluates AI agents on employee-level operational tasks. It measures how well AI agents can perform the same complex decision-making tasks that employees handle daily.

## Benchmark Features

- **Dashboard**: Monitor AI agent performance metrics in real-time
- **Benchmark Runner**: Execute benchmark tasks and test AI agents
- **Leaderboard**: Track and compare AI agent scores and rankings
- **Documentation**: Comprehensive guides for benchmarking AI systems
- **Modern Design**: Beautiful UI with Tailwind CSS and Framer Motion animations

## Benchmark Tasks

- **Easy**: Email Classification (75% baseline)
- **Medium**: Multi-Modal Operations (64% baseline)
- **Hard**: Comprehensive Management (66% baseline)

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Environment

Make sure the FastAPI backend is running on `http://localhost:7860`

## Tech Stack

- React 18
- Vite
- Tailwind CSS
- Framer Motion
- Axios
- Zustand
- Lucide Icons
- Recharts
