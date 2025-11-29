import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { projectsAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Detail.css'

const ProjectDetail = () => {
  const { id } = useParams()
  const { isDev } = useAuth()

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const response = await projectsAPI.get(id)
      return response.data
    },
  })

  if (isLoading) return <div className="loading">Загрузка проекта...</div>
  if (error) return <div className="error">Ошибка загрузки проекта: {error.message}</div>
  if (!project) return <div className="error">Проект не найден</div>

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <Link to="/projects" className="back-link">← Назад к проектам</Link>
          <h1>{project.name}</h1>
        </div>
        <span className="completion-badge-large">{project.completion_percent}%</span>
      </div>

      <div className="detail-grid">
        <div className="detail-section">
          <h2>Информация о проекте</h2>

          {!isDev() && project.customer_name && (
            <div className="field">
              <label>Заказчик</label>
              <div className="value">{project.customer_name}</div>
            </div>
          )}

          {!isDev() && project.total_cost && (
            <div className="field">
              <label>Общая стоимость</label>
              <div className="value">${project.total_cost}</div>
            </div>
          )}

          <div className="field">
            <label>Срок сдачи</label>
            <div className="value">{project.deadline}</div>
          </div>

          <div className="field">
            <label>Завершено</label>
            <div className="value">{project.completion_percent}%</div>
          </div>

          {project.responsible_details && (
            <div className="field">
              <label>Ответственный</label>
              <div className="value">{project.responsible_details.username}</div>
            </div>
          )}

          {project.active_stage && (
            <div className="field">
              <label>Текущий этап</label>
              <div className="value stage-badge">{project.active_stage}</div>
            </div>
          )}
        </div>

        <div className="detail-section">
          <h2>Разработчики ({project.developers_count || 0})</h2>
          {project.developers_details && project.developers_details.length > 0 ? (
            <div className="developers-list">
              {project.developers_details.map((dev) => (
                <Link key={dev.id} to={`/developers/${dev.id}`} className="developer-item">
                  <div>
                    <strong>{dev.full_name}</strong>
                    <span className="position">{dev.position}</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p>Разработчики не назначены</p>
          )}
        </div>
      </div>

      {project.stages && Array.isArray(project.stages) && project.stages.length > 0 && (
        <div className="detail-section">
          <h2>Этапы проекта</h2>
          <div className="stages-list">
            {project.stages.map((stage, index) => (
              <div key={index} className="stage-item">
                <strong>{stage.name || `Этап ${index + 1}`}</strong>
                {stage.status && <span className="status-badge">{stage.status}</span>}
                {stage.deadline && <span className="stage-deadline">Срок: {stage.deadline}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {project.comments && (
        <div className="detail-section">
          <h2>Комментарии</h2>
          <p className="comments">{project.comments}</p>
        </div>
      )}
    </div>
  )
}

export default ProjectDetail
