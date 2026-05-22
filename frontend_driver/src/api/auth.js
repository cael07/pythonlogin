import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://pythonlogin-api.onrender.com/auth',
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
      user: {
        full_name: formData.full_name,
        username: formData.username,
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirm_password,
        role: formData.role || 'driver',
        license_number: formData.license_number || null,
        or_renewal_date: formData.or_renewal_date || null,
        cr_plate_number: formData.cr_plate_number || null,
        cr_brand: formData.cr_brand || null,
        cr_color: formData.cr_color || null,
        cr_model: formData.cr_model || null,
        cr_owner_name: formData.cr_owner_name || null,
      },
      face_image: faceImage || null,
      license_image: formData.license_image || null,
      or_image: formData.or_image || null,
      cr_image: formData.cr_image || null,
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
