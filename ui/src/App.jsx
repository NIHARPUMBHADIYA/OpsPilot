import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Benchmark from './pages/Benchmark'
import Leaderboard from './pages/Leaderboard'
import Documentation from './pages/Documentation'
import { useStore } from './store'

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { apiConnected, checkConnection } = useStore()

  useEffect(() => {
    checkConnection()
  }, [])

  const pages = {
    dashboard: <Dashboard />,
    benchmark: <Benchmark />,
    leaderboard: <Leaderboard />,
    documentation: <Documentation />,
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Desktop Sidebar - always visible */}
      <div className="hidden md:block w-64 flex-shrink-0">
        <Sidebar open={true} setOpen={setSidebarOpen} currentPage={currentPage} setCurrentPage={setCurrentPage} />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
        />
      )}

      {/* Mobile Sidebar */}
      <motion.div
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen ? 0 : -300 }}
        transition={{ duration: 0.3 }}
        className="fixed left-0 top-0 w-64 h-screen z-40 md:hidden"
      >
        <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} currentPage={currentPage} setCurrentPage={setCurrentPage} />
      </motion.div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar 
          onMenuClick={() => setSidebarOpen(!sidebarOpen)} 
          apiConnected={apiConnected}
          currentPage={currentPage}
          onNavigate={setCurrentPage}
        />
        
        <main className="flex-1 overflow-auto">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="p-8"
          >
            {pages[currentPage]}
          </motion.div>
        </main>
      </div>
    </div>
  )
}
