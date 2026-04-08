import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:7860'

export function useRealtimeData(autoRefresh = true, refreshInterval = 5000) {
  const [stats, setStats] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [health, setHealth] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch all real-time data
  const fetchAllData = async () => {
    try {
      const [healthRes, leaderboardRes] = await Promise.all([
        axios.get(`${API_BASE}/health`),
        axios.get(`${API_BASE}/leaderboard`)
      ])

      setHealth(healthRes.data)
      setStats(healthRes.data)
      setLeaderboard(leaderboardRes.data.leaderboard || [])
      setError(null)
    } catch (err) {
      setError('Failed to fetch real-time data: ' + err.message)
      console.error('Real-time data fetch error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchAllData()
  }, [])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(fetchAllData, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])
}
