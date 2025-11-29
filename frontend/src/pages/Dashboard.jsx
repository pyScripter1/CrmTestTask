import { useQuery } from '@tanstack/react-query'
import { projectsAPI, developersAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'
import './Dashboard.css'

const Dashboard = () => {
  const { user, isAdmin, isPM } = useAuth()

  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await projectsAPI.list()
      return response.data
    },
  })

  const { data: developersData, isLoading: developersLoading } = useQuery({
    queryKey: ['developers'],
    queryFn: async () => {
      const response = await developersAPI.list()
      return response.data
    },
  })

  const projects = projectsData?.results || []
  const developers = developersData?.results || []

  return (
    <div className="dashboard">
      <h1>Панель управления</h1>
      <p className="welcome">Добро пожаловать, {user?.first_name || user?.username}!</p>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Всего проектов</h3>
          <div className="stat-number">{projects.length}</div>
          <Link to="/projects" className="stat-link">Посмотреть все проекты →</Link>
        </div>

        <div className="stat-card">
          <h3>Всего разработчиков</h3>
          <div className="stat-number">{developers.length}</div>
          <Link to="/developers" className="stat-link">Посмотреть всех разработчиков →</Link>
        </div>

        <div className="stat-card">
          <h3>Ваша роль</h3>
          <div className="stat-role">{user?.role}</div>
          <p className="stat-description">
            {isAdmin() && 'Полный доступ ко всем данным'}
            {isPM() && 'Управление вашими проектами'}
            {!isAdmin() && !isPM() && 'Просмотр назначенных проектов'}
          </p>
        </div>
      </div>

      <div className="recent-section">
        <h2>Недавние проекты</h2>
        {projectsLoading ? (
          <p>Загрузка...</p>
        ) : (
          <div className="recent-list">
            {projects.slice(0, 5).map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="recent-item">
                <div>
                  <strong>{project.name}</strong>
                  <span className="completion">{project.completion_percent}% завершено</span>
                </div>
                <span className="deadline">Срок: {project.deadline}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
