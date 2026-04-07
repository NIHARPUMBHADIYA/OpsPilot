import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Trophy, Medal, TrendingUp, RefreshCw } from 'lucide-react'
import { useRealtimeData } from '../hooks/useRealtimeData'

export default function Leaderboard() {
  const { leaderboard, isLoading, error, refresh } = useRealtimeData(true, 5000)
  const [sortBy, setSortBy] = useState('score')

  const getMedalIcon = (rank) => {
    if (rank === 1) return <Trophy className="text-yellow-400" size={20} />
    if (rank === 2) return <Medal className="text-slate-300" size={20} />
    if (rank === 3) return <Medal className="text-orange-400" size={20} />
    return <span className="text-slate-400 font-semibold">#{rank}</span>
  }

  const sortedLeaderboard = [...leaderboard].sort((a, b) => {
    if (sortBy === 'score') return b.score - a.score
    if (sortBy === 'name') return a.agent_name.localeCompare(b.agent_name)
    return new Date(b.timestamp) - new Date(a.timestamp)
  })

  return (
    <div className="space-y-8">
      <motion.div 
        initial={{ opacity: 0, y: -20 }} 
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Leaderboard</h1>
          <p className="text-slate-400">Top performing agents on OpsPilot++ (Live)</p>
        </div>
        <motion.button
          whileHover={{ rotate: 180 }}
          onClick={refresh}
          className="p-3 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw size={24} className="text-slate-300" />
        </motion.button>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card bg-red-500/10 border-red-500/30"
        >
          <p className="text-red-300">{error}</p>
        </motion.div>
      )}

      {/* Sort Controls */}
      <div className="flex gap-3">
        {['score', 'name', 'recent'].map((option) => (
          <button
            key={option}
            onClick={() => setSortBy(option)}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              sortBy === option
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {option.charAt(0).toUpperCase() + option.slice(1)}
          </button>
        ))}
      </div>

      {/* Leaderboard Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card overflow-hidden"
      >
        {isLoading ? (
          <div className="text-center py-12">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity }}
              className="inline-block"
            >
              <RefreshCw size={32} className="text-blue-400" />
            </motion.div>
            <p className="text-slate-400 mt-4">Loading leaderboard...</p>
          </div>
        ) : leaderboard.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-slate-400">No scores submitted yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Rank
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Agent Name
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Score
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                    Submitted
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedLeaderboard.map((entry, idx) => (
                  <motion.tr
                    key={entry.id || idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {getMedalIcon(idx + 1)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-white">{entry.agent_name}</span>
                    </td>
                    <td className="px-6 py-4">
                      <motion.div 
                        className="flex items-center gap-2"
                        key={entry.score}
                        initial={{ scale: 1.2 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.3 }}
                      >
                        <span className="text-lg font-bold text-green-400">
                          {(entry.score * 100).toFixed(1)}%
                        </span>
                        <TrendingUp size={16} className="text-green-400" />
                      </motion.div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric'
                      }) : 'N/A'}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Baseline Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card bg-gradient-to-br from-blue-600/20 to-purple-600/20 border-blue-500/30"
      >
        <h2 className="text-xl font-bold text-white mb-4">Baseline Scores</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-700/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-2">Easy Task</p>
            <p className="text-2xl font-bold text-green-400">75%</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-2">Medium Task</p>
            <p className="text-2xl font-bold text-yellow-400">64%</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm mb-2">Hard Task</p>
            <p className="text-2xl font-bold text-orange-400">66%</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
