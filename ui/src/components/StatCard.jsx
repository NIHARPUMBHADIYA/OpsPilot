import React from 'react'
import { motion } from 'framer-motion'

export default function StatCard({ icon: Icon, label, value, unit = '', trend = null, color = 'blue' }) {
  const colorClasses = {
    blue: 'from-blue-600/20 to-blue-400/10 border-blue-500/30',
    green: 'from-green-600/20 to-green-400/10 border-green-500/30',
    purple: 'from-purple-600/20 to-purple-400/10 border-purple-500/30',
    orange: 'from-orange-600/20 to-orange-400/10 border-orange-500/30',
  }

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`card bg-gradient-to-br ${colorClasses[color]} border`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium mb-2">{label}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{value}</span>
            {unit && <span className="text-slate-400 text-sm">{unit}</span>}
          </div>
          {trend && (
            <p className={`text-xs mt-2 ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last run
            </p>
          )}
        </div>
        <div className="p-3 bg-slate-700/50 rounded-lg">
          <Icon size={24} className="text-slate-300" />
        </div>
      </div>
    </motion.div>
  )
}
