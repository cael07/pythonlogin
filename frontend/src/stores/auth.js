import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  function getStoredUser() {
    try {
      const stored = localStorage.getItem('user')
      if (!stored || stored === 'undefined') return null
      return JSON.parse(stored)
    } catch (e) {
      return null
    }
  }

  const token = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(getStoredUser())

  const isAuthenticated = computed(() => !!token.value)

  function setAuth(data) {
    if (!data) return
    token.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = data.user || null
    
    if (data.access_token) localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
    if (data.user) localStorage.setItem('user', JSON.stringify(data.user))
  }

  function logout() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function login(username, password, appId = null, faceImage = null) {
    const data = await authApi.login({ username, password, face_image: faceImage }, appId)
    setAuth(data)
    return data
  }

  async function register(formData, faceImage, appId = null) {
    try {
      const data = await authApi.register(formData, faceImage, appId)
      setAuth(data)
      return data
    } catch (err) {
      console.error('Store Register Error:', err)
      throw err
    }
  }

  return { token, user, isAuthenticated, login, register, logout }
})
