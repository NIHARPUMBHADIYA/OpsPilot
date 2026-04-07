import React from 'react'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Zap,
  Trophy,
  BookOpen,
  ChevronRight,
} from 'lucide-react'

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'benchmark', label: 'Benchmark', icon: Zap },
  { id: 'leaderboard', label: 'Leaderboard', icon: Trophy },
  { id: 'documentation', label: 'Documentation', icon: BookOpen },
]

export default function Sidebar({ open, setOpen, currentPage, setCurrentPage }) {
  return (
    <div className="w-64 bg-slate-800/50 backdrop-blur-sm border-r border-slate-700/50 p-6 flex flex-col h-screen">
      <div className="space-y-8 flex-1">
        <div>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Menu
          </h2>
          <nav className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = currentPage === item.id
              return (
                <motion.button
                  key={item.id}
                  onClick={() => {
                    setCurrentPage(item.id)
                    setOpen(false)
                  }}
                  whileHover={{ x: 4 }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                      : 'text-slate-300 hover:bg-slate-700/30'
                  }`}
                >
                  <Icon size={20} />
                  <span className="font-medium">{item.label}</span>
                  {isActive && <ChevronRight size={16} className="ml-auto" />}
                </motion.button>
              )
            })}
          </nav>
        </div>
      </div>

      <div className="pt-6 border-t border-slate-700/50">
        <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-lg p-4">
          <p className="text-sm text-slate-300 mb-2">
            <span className="font-semibold">Tip:</span> Use the benchmark to evaluate your AI agents
          </p>
        </div>
      </div>
    </div>
  )
}
