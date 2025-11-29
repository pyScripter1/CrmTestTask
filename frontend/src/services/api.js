import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  logout: () => api.post('/auth/logout/'),
  me: () => api.get('/auth/me/'),
}

// Projects API
export const projectsAPI = {
  list: (params) => api.get('/projects/', { params }),
  get: (id) => api.get(`/projects/${id}/`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.put(`/projects/${id}/`, data),
  partialUpdate: (id, data) => api.patch(`/projects/${id}/`, data),
  delete: (id) => api.delete(`/projects/${id}/`),
  getDevelopers: (id) => api.get(`/projects/${id}/developers/`),
}

// Developers API
export const developersAPI = {
  list: (params) => api.get('/developers/', { params }),
  get: (id) => api.get(`/developers/${id}/`),
  create: (data) => api.post('/developers/', data),
  update: (id, data) => api.put(`/developers/${id}/`, data),
  partialUpdate: (id, data) => api.patch(`/developers/${id}/`, data),
  delete: (id) => api.delete(`/developers/${id}/`),
  getProjects: (id) => api.get(`/developers/${id}/projects/`),
}

export default api
