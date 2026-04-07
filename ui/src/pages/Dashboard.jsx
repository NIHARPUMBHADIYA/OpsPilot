import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, TrendingUp, Clock, Zap, RefreshCw } from 'lucide-react'
import StatCard from '../components/StatCard'
import axios from 'axios'

const API_BASE = 'http://localhost:7860'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch health and stats
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`)
      setStats(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch stats: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch leaderboard
  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get(`${API_BASE}/leaderboard`)
      setLeaderboard(response.data.leaderboard || [])
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchStats()
    fetchLeaderboard()
  }, [])

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchStats()
      fetchLeaderboard()
    }, 5000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-400">Real-time AI agent performance monitoring</p>
        </div>
        <motion.button
          whileHover={{ rotate: 180 }}
          onClick={() => {
            fetchStats()
            fetchLeaderboard()
          }}
          className="p-3 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw size={24} className="text-slate-300" />
        </motion.button>
      </motion.div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card bg-red-500/10 border-red-500/30"
        >
          <p className="text-red-300">{error}</p>
        </motion.div>
      )}

      {/* System Status */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <StatCard
            icon={Activity}
            label="API Status"
            value={stats.status === 'healthy' ? 'Healthy' : 'Error'}
            color={stats.status === 'healthy' ? 'green' : 'red'}
          />
          <StatCard
            icon={TrendingUp}
            label="Total Benchmarks"
            value={stats.total_benchmarks || 0}
            color="blue"
          />
          <StatCard
            icon={Clock}
            label="Avg Score"
            value={stats.average_score ? (stats.average_score * 100).toFixed(1) : '—'}
            unit="%"
            color="purple"
          />
          <StatCard
            icon={Zap}
            label="Active Sessions"
            value={stats.active_sessions || 0}
            color="orange"
          />
        </motion.div>
      )}

      {/* Auto-Refresh Toggle */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-4"
      >
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="text-slate-300">Auto-refresh every 5 seconds</span>
        </label>
      </motion.div>

      {/* Leaderboard */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <h2 className="text-2xl font-bold text-white mb-6">Top Agents</h2>
        
        {leaderboard.length > 0 ? (
          <div className="space-y-3">
            {leaderboard.slice(0, 5).map((entry, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-bold text-white">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="font-semibold text-white">{entry.agent_name}</p>
                    <p className="text-sm text-slate-400">Score: {(entry.score * 100).toFixed(1)}%</p>
                  </div>
                </div>
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-2xl font-bold text-green-400"
                >
                  {(entry.score * 100).toFixed(1)}%
                </motion.div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-slate-400">No benchmarks yet. Start a benchmark to see results!</p>
          </div>
        )}
      </motion.div>

      {/* System Info */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card bg-slate-700/20"
        >
          <h3 className="text-lg font-bold text-white mb-4">System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-400">Last Updated</p>
              <p className="text-white font-mono">{stats.timestamp ? new Date(stats.timestamp).toLocaleString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
              }) : 'N/A'}</p>
            </div>
            <div>
              <p className="text-slate-400">Environment Status</p>
              <p className="text-white">{stats.environment_status || 'Ready'}</p>
            </div>
          </div>
        </motion.div>
      )}

      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-8"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity }}
            className="inline-block"
          >
            <RefreshCw size={32} className="text-blue-400" />
          </motion.div>
          <p className="text-slate-400 mt-4">Loading dashboard...</p>
        </motion.div>
      )}
    </div>
  )
}
