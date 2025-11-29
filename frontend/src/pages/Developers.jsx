import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { developersAPI } from '../services/api'
import './List.css'

const Developers = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['developers'],
    queryFn: async () => {
      const response = await developersAPI.list()
      return response.data
    },
  })

  const developers = data?.results || []

  if (isLoading) return <div className="loading">Загрузка разработчиков...</div>
  if (error) return <div className="error">Ошибка загрузки разработчиков: {error.message}</div>

  return (
    <div className="list-page">
      <div className="list-header">
        <h1>Разработчики</h1>
        <p>Всего разработчиков: {developers.length}</p>
      </div>

      <div className="list-grid">
        {developers.map((developer) => (
          <Link key={developer.id} to={`/developers/${developer.id}`} className="list-card">
            <div className="card-header">
              <h3>{developer.full_name}</h3>
            </div>

            <div className="card-body">
              <p className="detail-row">
                <span className="label">Должность:</span>
                <span>{developer.position}</span>
              </p>

              {developer.cooperation_format && (
                <p className="detail-row">
                  <span className="label">Тип:</span>
                  <span className="format-badge">{developer.cooperation_format}</span>
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>

      {developers.length === 0 && (
        <div className="empty-state">
          <p>Разработчики не найдены</p>
        </div>
      )}
    </div>
  )
}

export default Developers
