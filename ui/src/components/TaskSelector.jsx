import React from 'react'
import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'

const tasks = [
  {
    id: 'easy',
    label: 'Easy',
    description: 'Email Classification',
    difficulty: '🟢',
    score: '75%',
  },
  {
    id: 'medium',
    label: 'Medium',
    description: 'Multi-Modal Operations',
    difficulty: '🟡',
    score: '64%',
  },
  {
    id: 'hard',
    label: 'Hard',
    description: 'Comprehensive Management',
    difficulty: '🔴',
    score: '66%',
  },
]

export default function TaskSelector({ selected, onSelect }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {tasks.map((task) => (
        <motion.button
          key={task.id}
          onClick={() => onSelect(task.id)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`card text-left transition-all ${
            selected === task.id
              ? 'ring-2 ring-blue-500 bg-blue-600/10'
              : 'hover:bg-slate-700/30'
          }`}
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-sm text-slate-400 mb-1">{task.difficulty}</p>
              <h3 className="text-lg font-bold text-white">{task.label}</h3>
            </div>
            <Zap size={20} className="text-blue-400" />
          </div>
          <p className="text-sm text-slate-300 mb-3">{task.description}</p>
          <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
            <span className="text-xs text-slate-400">Baseline</span>
            <span className="text-sm font-semibold text-green-400">{task.score}</span>
          </div>
        </motion.button>
      ))}
    </div>
  )
}
