import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('authToken')
    const savedUser = localStorage.getItem('user')

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (err) {
        console.error('Failed to parse user data:', err)
        localStorage.removeItem('user')
        localStorage.removeItem('authToken')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    try {
      setError(null)
      setLoading(true)

      const response = await authAPI.login({ username, password })
      const { token, user: userData } = response.data

      localStorage.setItem('authToken', token)
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)

      return { success: true }
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Login failed'
      setError(errorMessage)
      return { success: false, error: errorMessage }
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
      setUser(null)
    }
  }

  const isAdmin = () => {
    return user?.role === 'ADMIN'
  }

  const isPM = () => {
    return user?.role === 'PM'
  }

  const isDev = () => {
    return user?.role === 'DEV'
  }

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin,
    isPM,
    isDev,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
