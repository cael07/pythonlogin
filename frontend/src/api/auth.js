import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/auth',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(Array.isArray(msg) ? msg[0]?.msg || msg[0] : msg))
  }
)

export const authApi = {
  async register(formData, faceImage, appId) {
    const { data } = await api.post('/register', {
      user: formData,
      face_image: faceImage || null,
      app_id: appId || null,
    })
    return data
  },

  async login(credentials, appId) {
    const params = appId ? { app_id: appId } : {}
    const { data } = await api.post('/login', credentials, { params })
    return data
  },

  async getMe() {
    const { data } = await api.get('/me')
    return data
  },

  async refresh(refreshToken) {
    const { data } = await api.post('/refresh', { refresh_token: refreshToken })
    return data
  },
}
