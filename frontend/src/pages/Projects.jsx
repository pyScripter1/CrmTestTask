import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { projectsAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './List.css'

const Projects = () => {
  const { isDev } = useAuth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await projectsAPI.list()
      return response.data
    },
  })

  const projects = data?.results || []

  if (isLoading) return <div className="loading">Загрузка проектов...</div>
  if (error) return <div className="error">Ошибка загрузки проектов: {error.message}</div>

  return (
    <div className="list-page">
      <div className="list-header">
        <h1>Проекты</h1>
        <p>Всего проектов: {projects.length}</p>
      </div>

      <div className="list-grid">
        {projects.map((project) => (
          <Link key={project.id} to={`/projects/${project.id}`} className="list-card">
            <div className="card-header">
              <h3>{project.name}</h3>
              <span className="completion-badge">{project.completion_percent}%</span>
            </div>

            <div className="card-body">
              {!isDev() && project.customer_name && (
                <p className="detail-row">
                  <span className="label">Заказчик:</span>
                  <span>{project.customer_name}</span>
                </p>
              )}

              <p className="detail-row">
                <span className="label">Срок:</span>
                <span>{project.deadline}</span>
              </p>

              {project.responsible_name && (
                <p className="detail-row">
                  <span className="label">Ответственный:</span>
                  <span>{project.responsible_name}</span>
                </p>
              )}

              <p className="detail-row">
                <span className="label">Разработчики:</span>
                <span>{project.developers_count}</span>
              </p>

              {project.active_stage && (
                <p className="detail-row">
                  <span className="label">Этап:</span>
                  <span className="stage-badge">{project.active_stage}</span>
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>

      {projects.length === 0 && (
        <div className="empty-state">
          <p>Проекты не найдены</p>
        </div>
      )}
    </div>
  )
}

export default Projects
