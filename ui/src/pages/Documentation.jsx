import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, Code, BookOpen, Zap, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react'
import { useRealtimeData } from '../hooks/useRealtimeData'

const docs = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: BookOpen,
    sections: [
      {
        heading: 'What is OpsPilot++?',
        content:
          'OpsPilot++ is a comprehensive AI benchmark system designed to evaluate intelligent agents on real-world operational decision-making tasks. It tests AI agents on employee-level operational tasks including email management, task prioritization, scheduling, and decision-making under constraints. The benchmark provides a realistic environment where agents must handle multiple concurrent tasks and make strategic decisions.',
      },
      {
        heading: 'Key Features',
        content:
          '• Real-time scoring across 4 metrics: Email Classification, Response Quality, Decision Making, and Scheduling Efficiency\n• Multiple difficulty levels: Easy, Medium, and Hard scenarios\n• Support for multiple AI models: Baseline agent and Ollama local LLMs\n• Leaderboard system to track and compare agent performance\n• Detailed performance breakdowns and analytics\n• Reproducible benchmarks with random seed control',
      },
      {
        heading: 'Quick Start',
        content:
          '1. Navigate to the Benchmark page\n2. Select your AI model (Baseline or Ollama)\n3. Choose a difficulty level (Easy, Medium, or Hard)\n4. Enter your agent name\n5. Click "Start Benchmark" to begin\n6. Execute actions based on observations\n7. Submit your final score to the leaderboard',
      },
      {
        heading: 'System Requirements',
        content:
          '• Python 3.8+\n• Node.js 16+ (for UI)\n• 4GB RAM minimum\n• For Ollama: 8GB RAM recommended\n• Internet connection for API endpoints\n• Modern web browser (Chrome, Firefox, Safari, Edge)',
      },
    ],
  },
  {
    id: 'api-reference',
    title: 'API Reference',
    icon: Code,
    sections: [
      {
        heading: 'POST /reset',
        content: 'Initialize a new benchmark environment.\n\nParameters:\n• max_steps (int): Maximum steps allowed (default: 50)\n• initial_emails (int): Number of initial emails (default: 3)\n• initial_tasks (int): Number of initial tasks (default: 2)\n• random_seed (int): Seed for reproducibility\n\nResponse: Returns initial observation and environment state',
      },
      {
        heading: 'POST /step',
        content: 'Execute an action in the environment.\n\nRequest body:\n{\n  "email_actions": [],\n  "task_priorities": [],\n  "scheduling": [],\n  "skip_ids": []\n}\n\nResponse: Returns new observation, reward, done flag, and step info',
      },
      {
        heading: 'GET /health',
        content: 'Check API health status.\n\nResponse includes:\n• API status (healthy/unhealthy)\n• Component status (environment, graders, baseline agent)\n• System information (timestamp, version, episode count)',
      },
      {
        heading: 'GET /leaderboard',
        content: 'Retrieve the current leaderboard.\n\nResponse: Returns list of all submitted scores sorted by performance, including agent names, scores, and timestamps',
      },
      {
        heading: 'POST /submit_score',
        content: 'Submit a benchmark score to the leaderboard.\n\nRequest body:\n{\n  "agent_name": "string",\n  "score": 0.0-1.0\n}\n\nResponse: Confirmation of score submission and leaderboard position',
      },
      {
        heading: 'GET /models',
        content: 'Get available AI models and their status.\n\nResponse includes:\n• Model availability (installed/not installed)\n• Installation commands for unavailable models\n• Model-specific information and requirements',
      },
    ],
  },
  {
    id: 'task-types',
    title: 'Task Types',
    icon: Zap,
    sections: [
      {
        heading: 'Easy: Email Classification',
        content:
          'Difficulty: 🟢 Beginner\n\nFocus: Basic email handling and response generation\n• 3 initial emails\n• 2 initial tasks\n• 30 maximum steps\n• Success criteria: >75% classification accuracy\n\nMetrics:\n• Email Classification: 40% weight\n• Response Quality: 30% weight\n• Decision Making: 20% weight\n• Scheduling: 10% weight\n\nBest for: Testing basic agent functionality and understanding the benchmark format',
      },
      {
        heading: 'Medium: Multi-Modal Operations',
        content:
          'Difficulty: 🟡 Intermediate\n\nFocus: Handle emails while managing task priorities\n• 5 initial emails\n• 4 initial tasks\n• 50 maximum steps\n• Success criteria: >65% overall score across all graders\n\nMetrics:\n• Email Classification: 25% weight\n• Response Quality: 25% weight\n• Decision Making: 30% weight\n• Scheduling: 20% weight\n\nBest for: Evaluating agents with multi-task handling capabilities',
      },
      {
        heading: 'Hard: Comprehensive Management',
        content:
          'Difficulty: 🔴 Advanced\n\nFocus: Excel across all operational dimensions simultaneously\n• 8 initial emails\n• 6 initial tasks\n• 80 maximum steps\n• Success criteria: >60% overall score with minimal penalties\n\nMetrics:\n• Email Classification: 20% weight\n• Response Quality: 20% weight\n• Decision Making: 30% weight\n• Scheduling: 30% weight\n\nBest for: Comprehensive evaluation of advanced agent capabilities',
      },
    ],
  },
  {
    id: 'models',
    title: 'AI Models',
    icon: Zap,
    sections: [
      {
        heading: 'Baseline Agent',
        content:
          'Type: Rule-based reference implementation\nStatus: Always available\nPerformance: ~72% average score\n\nCharacteristics:\n• Deterministic decision-making\n• Fast execution\n• Good for benchmarking comparisons\n• No external dependencies\n\nUse case: Establish baseline performance metrics and validate benchmark correctness',
      },
      {
        heading: 'Ollama (Local LLM)',
        content:
          'Type: Local language model via Ollama\nStatus: Requires installation\nModels: llama2, mistral\n\nRequirements:\n• Ollama installed and running\n• 8GB+ RAM recommended\n• GPU support optional but recommended\n\nInstallation:\n• Windows: winget install ollama\n• macOS: brew install ollama\n• Linux: curl -fsSL https://ollama.ai/install.sh | sh\n\nAfter installation, run: ollama serve',
      },
      {
        heading: 'Model Comparison',
        content:
          'Baseline Agent:\n• Speed: Very Fast\n• Accuracy: Moderate\n• Resource Usage: Minimal\n• Customization: Limited\n\nOllama LLM:\n• Speed: Moderate\n• Accuracy: High\n• Resource Usage: High\n• Customization: High\n\nChoose Baseline for quick testing, Ollama for advanced evaluation',
      },
    ],
  },
  {
    id: 'scoring',
    title: 'Scoring System',
    icon: Zap,
    sections: [
      {
        heading: 'Email Classification Score',
        content:
          'Measures: Accuracy of email categorization and routing\nRange: 0-100%\n\nFactors:\n• Correct category assignment\n• Appropriate priority level\n• Relevant response generation\n• Handling of edge cases\n\nHow to improve:\n• Analyze email content patterns\n• Implement robust classification logic\n• Handle ambiguous cases gracefully',
      },
      {
        heading: 'Response Quality Score',
        content:
          'Measures: Quality and appropriateness of generated responses\nRange: 0-100%\n\nFactors:\n• Response relevance\n• Tone appropriateness\n• Completeness of information\n• Grammar and clarity\n\nHow to improve:\n• Use context-aware response generation\n• Implement quality checks\n• Test with diverse email types',
      },
      {
        heading: 'Decision Making Score',
        content:
          'Measures: Quality of strategic decisions under constraints\nRange: 0-100%\n\nFactors:\n• Optimal action selection\n• Resource allocation efficiency\n• Risk assessment accuracy\n• Constraint adherence\n\nHow to improve:\n• Implement decision trees\n• Use heuristic optimization\n• Consider multiple scenarios',
      },
      {
        heading: 'Scheduling Efficiency Score',
        content:
          'Measures: Effectiveness of meeting and task scheduling\nRange: 0-100%\n\nFactors:\n• Calendar optimization\n• Conflict avoidance\n• Time slot utilization\n• Priority alignment\n\nHow to improve:\n• Implement scheduling algorithms\n• Consider time zones and availability\n• Balance workload distribution',
      },
    ],
  },
  {
    id: 'best-practices',
    title: 'Best Practices',
    icon: BookOpen,
    sections: [
      {
        heading: 'Agent Development',
        content:
          '1. Start with Easy difficulty to understand the benchmark\n2. Analyze observation structure carefully\n3. Implement robust error handling\n4. Test with multiple random seeds\n5. Monitor all 4 scoring metrics\n6. Iterate based on feedback\n7. Document your approach\n8. Compare with baseline performance',
      },
      {
        heading: 'Performance Optimization',
        content:
          '1. Profile your agent code\n2. Optimize decision-making logic\n3. Cache frequently used computations\n4. Use efficient data structures\n5. Minimize API calls\n6. Implement early stopping when appropriate\n7. Balance accuracy vs. speed\n8. Test on all difficulty levels',
      },
      {
        heading: 'Debugging Tips',
        content:
          '1. Enable detailed logging\n2. Print observations at each step\n3. Validate action format\n4. Check score breakdowns\n5. Compare with baseline behavior\n6. Test edge cases\n7. Use smaller scenarios first\n8. Review error messages carefully',
      },
      {
        heading: 'Leaderboard Strategy',
        content:
          '1. Achieve consistent performance\n2. Test on all difficulty levels\n3. Submit multiple runs\n4. Track performance trends\n5. Learn from top performers\n6. Document your methodology\n7. Share insights with community\n8. Continuously improve your approach',
      },
    ],
  },
]

export default function Documentation() {
  const [expandedDoc, setExpandedDoc] = useState('getting-started')
  const [expandedSection, setExpandedSection] = useState({})
  const { health, error, refresh } = useRealtimeData(true, 10000)

  const toggleSection = (docId, sectionIdx) => {
    const key = `${docId}-${sectionIdx}`
    setExpandedSection((prev) => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  return (
    <div className="space-y-8">
      <motion.div 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Documentation</h1>
          <p className="text-slate-400">Learn how to use OpsPilot++ and build your agent</p>
        </div>
        <motion.button
          whileHover={{ rotate: 180 }}
          onClick={refresh}
          className="p-3 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw size={24} className="text-slate-300" />
        </motion.button>
      </motion.div>

      {/* System Status */}
      {health && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-gradient-to-br from-green-600/20 to-emerald-600/20 border-green-500/30"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="text-green-400" size={24} />
              <div>
                <h3 className="font-semibold text-white">System Status</h3>
                <p className="text-sm text-slate-400">API is healthy and responding</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-400">Last updated</p>
              <p className="text-white font-mono text-sm">{health.timestamp ? new Date(health.timestamp).toLocaleString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit'
              }) : 'N/A'}</p>
            </div>
          </div>
        </motion.div>
      )}

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card bg-red-500/10 border-red-500/30 flex items-center gap-3"
        >
          <AlertCircle className="text-red-400" size={24} />
          <p className="text-red-300">{error}</p>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-1"
        >
          <div className="card sticky top-8">
            <h3 className="font-semibold text-white mb-4">Documentation</h3>
            <nav className="space-y-2">
              {docs.map((doc) => {
                const Icon = doc.icon
                return (
                  <button
                    key={doc.id}
                    onClick={() => setExpandedDoc(doc.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-left ${
                      expandedDoc === doc.id
                        ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                        : 'text-slate-300 hover:bg-slate-700/30'
                    }`}
                  >
                    <Icon size={18} />
                    <span className="font-medium">{doc.title}</span>
                  </button>
                )
              })}
            </nav>
          </div>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-3 space-y-4"
        >
          {docs
            .filter((doc) => doc.id === expandedDoc)
            .map((doc) => (
              <div key={doc.id} className="space-y-4">
                {doc.sections.map((section, idx) => {
                  const key = `${doc.id}-${idx}`
                  const isExpanded = expandedSection[key]

                  return (
                    <motion.div
                      key={key}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="card"
                    >
                      <button
                        onClick={() => toggleSection(doc.id, idx)}
                        className="w-full flex items-center justify-between text-left"
                      >
                        <h3 className="text-lg font-semibold text-white">{section.heading}</h3>
                        <motion.div
                          animate={{ rotate: isExpanded ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown size={20} className="text-slate-400" />
                        </motion.div>
                      </button>

                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{
                          height: isExpanded ? 'auto' : 0,
                          opacity: isExpanded ? 1 : 0,
                        }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <p className="text-slate-300 mt-4">{section.content}</p>
                      </motion.div>
                    </motion.div>
                  )
                })}
              </div>
            ))}
        </motion.div>
      </div>
    </div>
  )
}
