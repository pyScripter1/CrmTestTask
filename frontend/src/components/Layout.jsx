import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Layout.css'

const Layout = () => {
  const { user, logout, isAdmin, isPM } = useAuth()
  const location = useLocation()

  const handleLogout = () => {
    logout()
  }

  const isActive = (path) => {
    return location.pathname.startsWith(path) ? 'active' : ''
  }

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <h1>CRM Система</h1>
        </div>
        <div className="navbar-menu">
          <Link to="/dashboard" className={`nav-link ${isActive('/dashboard')}`}>
            Панель управления
          </Link>
          <Link to="/projects" className={`nav-link ${isActive('/projects')}`}>
            Проекты
          </Link>
          <Link to="/developers" className={`nav-link ${isActive('/developers')}`}>
            Разработчики
          </Link>
        </div>
        <div className="navbar-user">
          <span className="user-info">
            {user?.username} <span className="user-role">({user?.role})</span>
          </span>
          <button onClick={handleLogout} className="logout-btn">
            Выход
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
