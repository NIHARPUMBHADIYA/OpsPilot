import { create } from 'zustand'
import axios from 'axios'

const API_BASE = 'http://localhost:7860'

export const useStore = create((set, get) => ({
  apiConnected: false,
  currentObservation: null,
  currentReward: null,
  leaderboard: [],
  taskType: 'easy',
  isLoading: false,
  error: null,

  checkConnection: async () => {
    try {
      await axios.get(`${API_BASE}/health`)
      set({ apiConnected: true, error: null })
    } catch (err) {
      set({ apiConnected: false, error: 'Failed to connect to API' })
    }
  },

  resetEnvironment: async (taskType = 'easy', seed = 42) => {
    set({ isLoading: true })
    try {
      const response = await axios.post(`${API_BASE}/reset`, {
        task_type: taskType,
        random_seed: seed,
      })
      set({
        currentObservation: response.data.observation,
        taskType,
        isLoading: false,
        error: null,
      })
      return response.data
    } catch (err) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },

  stepEnvironment: async (action) => {
    set({ isLoading: true })
    try {
      const response = await axios.post(`${API_BASE}/step`, action)
      set({
        currentObservation: response.data.observation,
        currentReward: response.data.reward,
        isLoading: false,
        error: null,
      })
      return response.data
    } catch (err) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },

  fetchLeaderboard: async () => {
    try {
      const response = await axios.get(`${API_BASE}/leaderboard`)
      set({ leaderboard: response.data.leaderboard || [] })
      return response.data
    } catch (err) {
      set({ error: err.message })
      throw err
    }
  },

  submitScore: async (agentName, score) => {
    try {
      const response = await axios.post(`${API_BASE}/submit_score`, {
        agent_name: agentName,
        score,
      })
      await get().fetchLeaderboard()
      return response.data
    } catch (err) {
      set({ error: err.message })
      throw err
    }
  },

  getExplanation: async () => {
    try {
      const response = await axios.get(`${API_BASE}/explain`)
      return response.data
    } catch (err) {
      set({ error: err.message })
      throw err
    }
  },

  getCounterfactual: async (action) => {
    try {
      const response = await axios.post(`${API_BASE}/counterfactual`, action)
      return response.data
    } catch (err) {
      set({ error: err.message })
      throw err
    }
  },
}))
