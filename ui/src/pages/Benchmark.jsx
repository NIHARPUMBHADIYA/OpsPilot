import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, RotateCcw, Send, Settings, Zap, Brain, AlertCircle, Copy, Check } from 'lucide-react'
import axios from 'axios'

const API_BASE = 'http://localhost:7860'

// Animated Progress Bar Component
function AnimatedProgressBar({ value, color, label }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-slate-300 font-medium">{label}</span>
        <motion.span 
          className="text-white font-bold text-lg"
          key={value}
          initial={{ scale: 1.2, color: '#60a5fa' }}
          animate={{ scale: 1, color: '#ffffff' }}
          transition={{ duration: 0.3 }}
        >
          {(value * 100).toFixed(0)}%
        </motion.span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
        <motion.div
          className={`h-3 rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

// Installation Prompt Component
function InstallationPrompt({ model, onClose }) {
  const [copiedIndex, setCopiedIndex] = useState(null)

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    >
      <motion.div
        className="bg-slate-800 rounded-lg border border-slate-700 max-w-xl w-full max-h-96 overflow-y-auto"
        initial={{ y: 20 }}
        animate={{ y: 0 }}
      >
        <div className="p-5 space-y-4">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">{model.name} Not Installed</h2>
            <p className="text-slate-400 text-sm">{model.description}</p>
          </div>

          {model.install_commands && model.install_commands.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-white mb-2">Step 1: Install Ollama</h3>
              <div className="space-y-1">
                {model.install_commands.map((cmd, idx) => (
                  <button
                    key={idx}
                    onClick={() => copyToClipboard(cmd, idx)}
                    className="w-full bg-slate-700 hover:bg-slate-600 rounded-lg p-2 text-left font-mono text-xs text-slate-300 transition-colors flex items-center justify-between group"
                  >
                    <span className="truncate">{cmd}</span>
                    {copiedIndex === idx ? (
                      <Check size={16} className="text-green-400 flex-shrink-0 ml-2" />
                    ) : (
                      <Copy size={16} className="text-slate-500 group-hover:text-slate-300 flex-shrink-0 ml-2" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {model.pull_commands && model.pull_commands.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-white mb-2">Step 2: Pull Models</h3>
              <div className="space-y-1">
                {model.pull_commands.map((cmd, idx) => (
                  <button
                    key={idx}
                    onClick={() => copyToClipboard(cmd, idx + 100)}
                    className="w-full bg-slate-700 hover:bg-slate-600 rounded-lg p-2 text-left font-mono text-xs text-slate-300 transition-colors flex items-center justify-between group"
                  >
                    <span className="truncate">{cmd}</span>
                    {copiedIndex === idx + 100 ? (
                      <Check size={16} className="text-green-400 flex-shrink-0 ml-2" />
                    ) : (
                      <Copy size={16} className="text-slate-500 group-hover:text-slate-300 flex-shrink-0 ml-2" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
            <p className="text-blue-300 text-xs">
              💡 After installation, run <code className="bg-slate-700 px-1 py-0.5 rounded text-xs">ollama serve</code> to start the service.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded-lg transition-colors text-sm"
          >
            Close
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default function Benchmark() {
  const [step, setStep] = useState('setup')
  const [selectedModel, setSelectedModel] = useState('baseline')
  const [selectedScenario, setSelectedScenario] = useState('easy')
  const [agentName, setAgentName] = useState('')
  const [actionInput, setActionInput] = useState('')
  const [results, setResults] = useState(null)
  const [currentObservation, setCurrentObservation] = useState(null)
  const [currentReward, setCurrentReward] = useState(null)
  const [error, setError] = useState(null)
  const [stepCount, setStepCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [models, setModels] = useState([])
  const [modelsLoading, setModelsLoading] = useState(true)
  const [showInstallPrompt, setShowInstallPrompt] = useState(null)
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)

  const scenarios = [
    { id: 'easy', name: 'Easy', desc: 'Email classification focus', difficulty: '🟢' },
    { id: 'medium', name: 'Medium', desc: 'Multi-modal operations', difficulty: '🟡' },
    { id: 'hard', name: 'Hard', desc: 'Comprehensive management', difficulty: '�' },
  ]

  // Fetch real-time model data
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await axios.get(`${API_BASE}/models`)
        const modelsData = response.data.models
        
        // Convert to array format
        const modelsArray = Object.entries(modelsData).map(([key, value]) => ({
          id: key,
          ...value
        }))
        
        setModels(modelsArray)
        setModelsLoading(false)
      } catch (err) {
        console.error('Failed to fetch models:', err)
        // Fallback to default models (only Baseline and Ollama)
        setModels([
          { id: 'baseline', name: 'Baseline Agent', description: 'Rule-based reference implementation', icon: '🤖', available: true },
          { id: 'ollama', name: 'Ollama (Local LLM)', description: 'Local language model via Ollama', icon: '🧠', available: false },
        ])
        setModelsLoading(false)
      }
    }

    fetchModels()
    
    // Refresh models every 10 seconds
    const interval = setInterval(fetchModels, 10000)
    return () => clearInterval(interval)
  }, [])

  // Fetch real-time stats data
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`)
        setStats(response.data)
        setStatsLoading(false)
      } catch (err) {
        console.error('Failed to fetch stats:', err)
        setStatsLoading(false)
      }
    }

    fetchStats()
    
    // Refresh stats every 5 seconds
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleStartBenchmark = async () => {
    if (!agentName.trim()) {
      setError('Please enter an agent name')
      return
    }

    setIsLoading(true)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE}/reset`, {
        max_steps: selectedScenario === 'easy' ? 30 : selectedScenario === 'medium' ? 50 : 80,
        initial_emails: selectedScenario === 'easy' ? 3 : selectedScenario === 'medium' ? 5 : 8,
        initial_tasks: selectedScenario === 'easy' ? 2 : selectedScenario === 'medium' ? 4 : 6,
        random_seed: Math.floor(Math.random() * 10000)
      })
      
      setCurrentObservation(response.data.observation)
      setCurrentReward(null)
      setStepCount(0)
      setStep('running')
    } catch (err) {
      setError('Failed to start benchmark: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  const handleExecuteAction = async () => {
    if (!actionInput.trim()) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const action = JSON.parse(actionInput)
      const response = await axios.post(`${API_BASE}/step`, action)
      
      setCurrentObservation(response.data.observation)
      setCurrentReward(response.data.reward)
      setStepCount(stepCount + 1)
      setActionInput('')
      
      if (response.data.done) {
        setTimeout(() => handleFinishBenchmark(response.data.reward), 1000)
      }
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid action JSON format')
      } else {
        setError('Failed to execute action: ' + (err.response?.data?.detail || err.message))
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleRunAgent = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE}/baseline`, {
        observation: currentObservation
      })
      
      const stepResponse = await axios.post(`${API_BASE}/step`, response.data.action)
      
      setCurrentObservation(stepResponse.data.observation)
      setCurrentReward(stepResponse.data.reward)
      setStepCount(stepCount + 1)
      
      if (stepResponse.data.done) {
        setTimeout(() => handleFinishBenchmark(stepResponse.data.reward), 1000)
      }
    } catch (err) {
      setError('Failed to run agent: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  const handleFinishBenchmark = async (finalReward = currentReward) => {
    setStep('results')
    
    setResults({
      agentName,
      model: selectedModel,
      scenario: selectedScenario,
      finalScore: finalReward?.score || 0,
      breakdown: {
        email: finalReward?.email_score || 0,
        response: finalReward?.response_score || 0,
        decision: finalReward?.decision_score || 0,
        scheduling: finalReward?.scheduling_score || 0,
      },
      steps: stepCount,
      timestamp: new Date().toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      })
    })
  }

  const handleSubmitScore = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      await axios.post(`${API_BASE}/submit_score`, {
        agent_name: results.agentName,
        score: results.finalScore
      })
      alert('Score submitted to leaderboard successfully!')
    } catch (err) {
      setError('Failed to submit score: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setStep('setup')
    setSelectedModel('baseline')
    setSelectedScenario('easy')
    setAgentName('')
    setActionInput('')
    setResults(null)
    setCurrentObservation(null)
    setCurrentReward(null)
    setError(null)
    setStepCount(0)
  }

  // SETUP STEP
  if (step === 'setup') {
    return (
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl font-bold text-white mb-2">Benchmark Setup</h1>
          <p className="text-slate-400">Configure and run your AI agent benchmark to evaluate operational decision-making</p>
        </motion.div>

        {/* Info Cards */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="card bg-blue-500/10 border-blue-500/30">
            <p className="text-xs text-blue-300 mb-1">📊 Total Benchmarks</p>
            {statsLoading ? (
              <p className="text-2xl font-bold text-blue-400 animate-pulse">--</p>
            ) : (
              <motion.p 
                className="text-2xl font-bold text-blue-400"
                key={stats?.total_benchmarks}
                initial={{ scale: 1.2 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                {stats?.total_benchmarks || 0}
              </motion.p>
            )}
            <p className="text-xs text-slate-400 mt-1">Completed this month</p>
          </div>
          <div className="card bg-green-500/10 border-green-500/30">
            <p className="text-xs text-green-300 mb-1">🎯 Avg Score</p>
            {statsLoading ? (
              <p className="text-2xl font-bold text-green-400 animate-pulse">--</p>
            ) : (
              <motion.p 
                className="text-2xl font-bold text-green-400"
                key={stats?.average_score}
                initial={{ scale: 1.2 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                {stats?.average_score ? (stats.average_score * 100).toFixed(1) : 0}%
              </motion.p>
            )}
            <p className="text-xs text-slate-400 mt-1">Across all agents</p>
          </div>
          <div className="card bg-purple-500/10 border-purple-500/30">
            <p className="text-xs text-purple-300 mb-1">⚡ Active Sessions</p>
            {statsLoading ? (
              <p className="text-2xl font-bold text-purple-400 animate-pulse">--</p>
            ) : (
              <motion.p 
                className="text-2xl font-bold text-purple-400"
                key={stats?.active_sessions}
                initial={{ scale: 1.2 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                {stats?.active_sessions || 0}
              </motion.p>
            )}
            <p className="text-xs text-slate-400 mt-1">Currently benchmarking</p>
          </div>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card bg-red-500/10 border-red-500/30">
            <div className="flex gap-3">
              <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          </motion.div>
        )}

        {/* Model Selection */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
          <div className="flex items-center gap-2 mb-4">
            <Brain size={20} className="text-blue-400" />
            <h2 className="text-xl font-bold text-white">Select Model</h2>
            <span className="text-xs text-slate-400 ml-auto">Choose your AI model</span>
          </div>
          
          {modelsLoading ? (
            <div className="text-center py-6">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity }}
                className="inline-block"
              >
                <Zap size={24} className="text-blue-400" />
              </motion.div>
              <p className="text-slate-400 text-sm mt-2">Loading models...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {models.map(model => (
                <button
                  key={model.id}
                  onClick={() => {
                    if (!model.available && model.install_commands) {
                      setShowInstallPrompt(model)
                    } else {
                      setSelectedModel(model.id)
                    }
                  }}
                  disabled={!model.available && model.install_commands}
                  className={`p-3 rounded-lg border-2 transition-all text-left text-sm ${
                    selectedModel === model.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : model.available
                      ? 'border-slate-600 bg-slate-700/30 hover:border-slate-500'
                      : 'border-slate-700 bg-slate-800/50 opacity-60 cursor-not-allowed'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 flex-1">
                      <span className="text-lg">{model.icon}</span>
                      <div className="min-w-0">
                        <p className="font-semibold text-white text-sm">{model.name}</p>
                        <p className="text-xs text-slate-400 line-clamp-1">{model.description}</p>
                      </div>
                    </div>
                    {model.available ? (
                      <span className="text-xs bg-green-500/20 text-green-300 px-2 py-1 rounded whitespace-nowrap">✓</span>
                    ) : model.install_commands ? (
                      <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded whitespace-nowrap">⚠</span>
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
          )}
          <p className="text-xs text-slate-500 mt-3">💡 Baseline is always available. Ollama requires local installation.</p>
        </motion.div>

        {/* Scenario Selection */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
          <div className="flex items-center gap-2 mb-4">
            <Settings size={20} className="text-purple-400" />
            <h2 className="text-xl font-bold text-white">Select Scenario</h2>
            <span className="text-xs text-slate-400 ml-auto">Task difficulty level</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {scenarios.map(scenario => (
              <button
                key={scenario.id}
                onClick={() => setSelectedScenario(scenario.id)}
                className={`p-3 rounded-lg border-2 transition-all text-left text-sm ${
                  selectedScenario === scenario.id
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-slate-600 bg-slate-700/30 hover:border-slate-500'
                }`}
              >
                <p className="font-semibold text-white">{scenario.difficulty} {scenario.name}</p>
                <p className="text-xs text-slate-400">{scenario.desc}</p>
              </button>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
            <div className="text-slate-400">
              <span className="text-green-400 font-semibold">Easy:</span> 3 emails, 2 tasks, 30 steps
            </div>
            <div className="text-slate-400">
              <span className="text-yellow-400 font-semibold">Medium:</span> 5 emails, 4 tasks, 50 steps
            </div>
            <div className="text-slate-400">
              <span className="text-orange-400 font-semibold">Hard:</span> 8 emails, 6 tasks, 80 steps
            </div>
          </div>
        </motion.div>

        {/* Agent Configuration */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h3 className="text-lg font-bold text-white mb-3">Agent Configuration</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Agent Name</label>
              <input
                type="text"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="e.g., MyAdvancedAgent, GPT-4-Optimizer"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
              />
              <p className="text-xs text-slate-500 mt-1">Give your agent a unique identifier for tracking</p>
            </div>
            
            <button
              onClick={handleStartBenchmark}
              disabled={!agentName.trim() || isLoading || !models.find(m => m.id === selectedModel)?.available}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              <Play size={18} />
              {isLoading ? 'Starting...' : 'Start Benchmark'}
            </button>
          </div>
        </motion.div>

        {/* What to Expect */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card bg-slate-700/30 border-slate-600">
          <h3 className="text-sm font-bold text-white mb-3">📋 What to Expect</h3>
          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex gap-2">
              <span className="text-blue-400">1.</span>
              <span>Your agent receives an observation with emails, tasks, and scheduling data</span>
            </div>
            <div className="flex gap-2">
              <span className="text-blue-400">2.</span>
              <span>Execute actions to classify emails, prioritize tasks, and schedule meetings</span>
            </div>
            <div className="flex gap-2">
              <span className="text-blue-400">3.</span>
              <span>Receive real-time scores across 4 metrics: Email, Response, Decision, Scheduling</span>
            </div>
            <div className="flex gap-2">
              <span className="text-blue-400">4.</span>
              <span>Submit your final score to the leaderboard and compare with other agents</span>
            </div>
          </div>
        </motion.div>

        {/* Installation Prompt Modal */}
        <AnimatePresence>
          {showInstallPrompt && (
            <InstallationPrompt 
              model={showInstallPrompt} 
              onClose={() => setShowInstallPrompt(null)}
            />
          )}
        </AnimatePresence>
      </div>
    )
  }

  // RUNNING STEP
  if (step === 'running') {
    return (
      <div className="space-y-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl font-bold text-white mb-2">Running Benchmark</h1>
          <p className="text-slate-400">Agent: {agentName} | Model: {selectedModel} | Scenario: {selectedScenario} | Step: {stepCount}</p>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card bg-red-500/10 border-red-500/30">
            <div className="flex gap-3">
              <AlertCircle className="text-red-400 flex-shrink-0" />
              <p className="text-red-300">{error}</p>
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2 space-y-6"
          >
            <div className="card">
              <h2 className="text-xl font-bold text-white mb-4">Current Observation</h2>
              <div className="bg-slate-700/30 rounded-lg p-4 font-mono text-sm text-slate-300 max-h-96 overflow-auto">
                {currentObservation ? (
                  <pre>{JSON.stringify(currentObservation, null, 2)}</pre>
                ) : (
                  <p className="text-slate-500">Loading observation...</p>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-bold text-white mb-4">Execute Action</h2>
              <textarea
                value={actionInput}
                onChange={(e) => setActionInput(e.target.value)}
                placeholder='{"email_actions": [], "task_priorities": [], "scheduling": [], "skip_ids": []}'
                className="input-field font-mono text-sm h-32 mb-4"
              />
              <div className="flex gap-3">
                <button
                  onClick={handleExecuteAction}
                  disabled={isLoading || !actionInput.trim()}
                  className="flex-1 bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send size={18} />
                  Execute
                </button>
                <button
                  onClick={handleRunAgent}
                  disabled={isLoading || !currentObservation}
                  className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Zap size={18} />
                  Auto Run
                </button>
              </div>
            </div>

            {/* API Request/Response */}
            <div className="card">
              <h2 className="text-xl font-bold text-white mb-4">API Request/Response</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-xs font-semibold text-slate-300 mb-2">📤 Request (POST /step)</p>
                  <div className="bg-slate-700/30 rounded-lg p-3 font-mono text-xs text-slate-300 max-h-40 overflow-auto border border-slate-600">
                    <pre className="whitespace-pre-wrap break-words">
                      {actionInput ? (
                        (() => {
                          try {
                            return JSON.stringify(JSON.parse(actionInput), null, 2)
                          } catch {
                            return '// Invalid JSON format'
                          }
                        })()
                      ) : '// Enter action above'}
                    </pre>
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-300 mb-2">📥 Response</p>
                  <div className="bg-slate-700/30 rounded-lg p-3 font-mono text-xs text-slate-300 max-h-40 overflow-auto border border-slate-600">
                    {currentReward ? (
                      <pre className="whitespace-pre-wrap break-words">
                        {JSON.stringify({
                          reward: currentReward,
                          done: false,
                          step: stepCount
                        }, null, 2)}
                      </pre>
                    ) : (
                      <p className="text-slate-500">// Response will appear here after executing an action</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-4"
          >
            {currentReward && (
              <motion.div 
                className="card bg-gradient-to-br from-green-600/20 to-green-400/10 border-green-500/30"
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <p className="text-slate-400 text-sm mb-4">Current Score</p>
                <motion.p 
                  className="text-5xl font-bold text-green-400 mb-6"
                  key={currentReward.score}
                  initial={{ scale: 1.2 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  {(currentReward.score * 100).toFixed(1)}%
                </motion.p>
                
                <div className="space-y-4">
                  <AnimatedProgressBar 
                    value={currentReward.email_score} 
                    color="bg-blue-500"
                    label="Email Classification"
                  />
                  <AnimatedProgressBar 
                    value={currentReward.response_score} 
                    color="bg-green-500"
                    label="Response Quality"
                  />
                  <AnimatedProgressBar 
                    value={currentReward.decision_score} 
                    color="bg-purple-500"
                    label="Decision Making"
                  />
                  <AnimatedProgressBar 
                    value={currentReward.scheduling_score} 
                    color="bg-orange-500"
                    label="Scheduling Efficiency"
                  />
                </div>
              </motion.div>
            )}

            {!currentReward && (
              <div className="card bg-slate-700/30 border-slate-600">
                <p className="text-slate-400 text-center py-8">Execute an action to see scores</p>
              </div>
            )}

            <div className="card space-y-3">
              <h3 className="font-semibold text-white">Actions</h3>
              <button
                onClick={() => handleFinishBenchmark()}
                className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <RotateCcw size={18} />
                Finish & Results
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    )
  }

  // RESULTS STEP
  if (step === 'results' && results) {
    return (
      <div className="space-y-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl font-bold text-white mb-2">Benchmark Results</h1>
          <p className="text-slate-400">{results.timestamp}</p>
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card bg-red-500/10 border-red-500/30">
            <div className="flex gap-3">
              <AlertCircle className="text-red-400 flex-shrink-0" />
              <p className="text-red-300">{error}</p>
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <div className="card bg-gradient-to-br from-blue-600/20 to-blue-400/10 border-blue-500/30">
              <h2 className="text-2xl font-bold text-white mb-6">Final Score</h2>
              <motion.p 
                className="text-6xl font-bold text-blue-400 mb-6"
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                {(results.finalScore * 100).toFixed(1)}%
              </motion.p>
              
              <div className="space-y-4">
                <AnimatedProgressBar 
                  value={results.breakdown.email} 
                  color="bg-blue-500"
                  label="Email Classification"
                />
                <AnimatedProgressBar 
                  value={results.breakdown.response} 
                  color="bg-green-500"
                  label="Response Quality"
                />
                <AnimatedProgressBar 
                  value={results.breakdown.decision} 
                  color="bg-purple-500"
                  label="Decision Making"
                />
                <AnimatedProgressBar 
                  value={results.breakdown.scheduling} 
                  color="bg-orange-500"
                  label="Scheduling Efficiency"
                />
              </div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <div className="card space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Agent Name</h3>
                <p className="text-xl font-bold text-white">{results.agentName}</p>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Model</h3>
                <p className="text-xl font-bold text-white capitalize">{results.model}</p>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Scenario</h3>
                <p className="text-xl font-bold text-white capitalize">{results.scenario}</p>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Steps Completed</h3>
                <p className="text-xl font-bold text-white">{results.steps}</p>
              </div>
              
              <button
                onClick={handleSubmitScore}
                disabled={isLoading}
                className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Submitting...' : 'Submit to Leaderboard'}
              </button>
              
              <button
                onClick={handleReset}
                className="w-full bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <RotateCcw size={18} />
                Run Another Benchmark
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    )
  }

  return null
}
