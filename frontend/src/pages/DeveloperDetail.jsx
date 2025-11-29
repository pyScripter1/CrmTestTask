import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { developersAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Detail.css'

const DeveloperDetail = () => {
  const { id } = useParams()
  const { isAdmin, isPM } = useAuth()

  const { data: developer, isLoading, error } = useQuery({
    queryKey: ['developer', id],
    queryFn: async () => {
      const response = await developersAPI.get(id)
      return response.data
    },
  })

  if (isLoading) return <div className="loading">Загрузка разработчика...</div>
  if (error) return <div className="error">Ошибка загрузки разработчика: {error.message}</div>
  if (!developer) return <div className="error">Разработчик не найден</div>

  return (
    <div className="detail-page">
      <div className="detail-header">
        <div>
          <Link to="/developers" className="back-link">← Назад к разработчикам</Link>
          <h1>{developer.full_name}</h1>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-section">
          <h2>Информация о разработчике</h2>

          <div className="field">
            <label>Должность</label>
            <div className="value">{developer.position}</div>
          </div>

          {developer.cooperation_format && (
            <div className="field">
              <label>Формат сотрудничества</label>
              <div className="value format-badge">{developer.cooperation_format}</div>
            </div>
          )}

          {isAdmin() && developer.salary && (
            <div className="field">
              <label>Зарплата</label>
              <div className="value">${developer.salary}</div>
            </div>
          )}

          {developer.workload && (
            <div className="field">
              <label>Загруженность</label>
              <div className="value">{developer.workload}</div>
            </div>
          )}

          {(isAdmin() || isPM()) && developer.contacts && (
            <div className="field">
              <label>Контакты</label>
              <div className="value">{developer.contacts}</div>
            </div>
          )}
        </div>

        <div className="detail-section">
          <h2>Навыки и компетенции</h2>

          {developer.competencies && (
            <div className="field">
              <label>Компетенции</label>
              <div className="value">{developer.competencies}</div>
            </div>
          )}

          {developer.strengths && (
            <div className="field">
              <label>Сильные стороны</label>
              <div className="value">{developer.strengths}</div>
            </div>
          )}

          {developer.weaknesses && (
            <div className="field">
              <label>Области для улучшения</label>
              <div className="value">{developer.weaknesses}</div>
            </div>
          )}
        </div>
      </div>

      {developer.comments && (
        <div className="detail-section">
          <h2>Комментарии</h2>
          <p className="comments">{developer.comments}</p>
        </div>
      )}

      {developer.projects_count > 0 && (
        <div className="detail-section">
          <h2>Проекты ({developer.projects_count})</h2>
          <p>Этот разработчик назначен на {developer.projects_count} проект(ов).</p>
        </div>
      )}
    </div>
  )
}

export default DeveloperDetail
