import React from 'react'
import { Menu, Zap, AlertCircle, ArrowLeft } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Navbar({ onMenuClick, apiConnected, currentPage, onNavigate }) {
  const pageNames = {
    dashboard: 'Dashboard',
    benchmark: 'Benchmark',
    leaderboard: 'Leaderboard',
    documentation: 'Documentation'
  }

  const handleBack = () => {
    // Navigate to dashboard
    if (onNavigate) {
      onNavigate('dashboard')
    }
  }

  return (
    <nav className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 px-8 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <Menu size={24} />
        </button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Zap size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">OpsPilot++</h1>
            <p className="text-xs text-slate-400">AI Operations Benchmark</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {currentPage && currentPage !== 'dashboard' && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleBack}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white transition-colors"
          >
            <ArrowLeft size={18} />
            <span className="text-sm font-medium">Back</span>
          </motion.button>
        )}

        <motion.div
          animate={{ scale: apiConnected ? 1 : 0.95 }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            apiConnected
              ? 'bg-green-500/20 text-green-300'
              : 'bg-red-500/20 text-red-300'
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full ${
              apiConnected ? 'bg-green-400' : 'bg-red-400'
            } animate-pulse`}
          />
          <span className="text-sm font-medium">
            {apiConnected ? 'Connected' : 'Disconnected'}
          </span>
        </motion.div>
      </div>
    </nav>
  )
}
