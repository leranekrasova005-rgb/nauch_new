import { useState, useEffect } from 'react'
import api from '../../services/api'
import { useToast } from '../../Toast'
import { Check, X, Users, FileText, Activity, Clock, Eye, MessageSquare } from 'lucide-react'
import './AdminPanel.css'

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  role_display: string
  is_active: boolean
  publications_count: number
}

interface DeleteRequest {
  id: number
  publication: number
  publication_title: string
  requester: number
  requester_username: string
  reason: string
  status: string
  status_display: string
  created_at: string
}

interface PublicationForModeration {
  id: number
  title: string
  author: string
  year: number
  department: string
  status: string
  status_display: string
  moderation_status: string
  moderation_status_display: string
  created_at: string
  updated_at: string
  owner: number
  owner_username: string
  moderated_by?: number | null
  moderated_at?: string | null
  moderation_comment?: string | null
}

const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'requests' | 'logs' | 'moderation'>('moderation')
  const [users, setUsers] = useState<User[]>([]);
  const [deleteRequests, setDeleteRequests] = useState<DeleteRequest[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [publicationsForModeration, setPublicationsForModeration] = useState<PublicationForModeration[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<number | null>(null)
  const [selectedPub, setSelectedPub] = useState<PublicationForModeration | null>(null)
  const [moderationComment, setModerationComment] = useState('')
  const toast = useToast()

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'users') {
        const response = await api.get('/users/users/')
        setUsers(response.data.results || response.data)
      } else if (activeTab === 'requests') {
        const response = await api.get('/delete-requests/')
        setDeleteRequests(response.data.results || response.data)
      } else if (activeTab === 'logs') {
        const response = await api.get('/activity-logs/')
        setLogs(response.data.results || response.data)
      } else if (activeTab === 'moderation') {
        const response = await api.get('/publications/?moderation_status=pending&page_size=100')
        setPublicationsForModeration([])
        setPublicationsForModeration(response.data.results || response.data)
      }
    } catch (error) {
      console.error('Error loading data:', error)
      toast.addToast({
        type: 'error',
        title: 'Ошибка загрузки',
        message: 'Не удалось загрузить данные'
      })
    } finally {
      setLoading(false)
    }
  }

  const updateUserRole = async (id: number, role: string) => {
    setUpdating(id)
    try {
      await api.patch(`/users/users/${id}/set_role_/`, { role })
      await loadData()
    } catch (error) {
      console.error('Error updating role:', error)
    } finally {
      setUpdating(null)
    }
  }

  const toggleUserActive = async (id: number, is_active: boolean) => {
    setUpdating(id)
    try {
      await api.patch(`/users/users/${id}/`, { is_active })
      await loadData()
    } catch (error) {
      console.error('Error toggling user:', error)
    } finally {
      setUpdating(null)
    }
  }

  const reviewDeleteRequest = async (id: number, status: string) => {
    setUpdating(id)
    try {
      await api.patch(`/delete-requests/${id}/`, { status })
      toast.addToast({
        type: 'success',
        title: 'Запрос обработан',
        message: `Запрос на удаление ${status === 'approved' ? 'одобрен' : 'отклонён'}`
      })
      await loadData()
    } catch (error) {
      console.error('Error reviewing request:', error)
      toast.addToast({
        type: 'error',
        title: 'Ошибка',
        message: 'Не удалось обработать запрос'
      })
    } finally {
      setUpdating(null)
    }
  }

  const moderatePublication = async (id: number, status: 'approved' | 'rejected') => {
    setUpdating(id)
    try {
      await api.post(`/publications/${id}/moderate/`, {
        status: status,
        comment: moderationComment || ''
      })
      toast.addToast({
        type: 'success',
        title: 'Модерация завершена',
        message: `Публикация ${status === 'approved' ? 'одобрена' : 'отклонена'}${moderationComment ? ' с комментарием' : ''}`
      })
      setModerationComment('')
      setSelectedPub(null)
      await loadData()
    } catch (error) {
      console.error('Error moderating publication:', error)
      toast.addToast({
        type: 'error',
        title: 'Ошибка модерации',
        message: 'Не удалось выполнить модерацию'
      })
    } finally {
      setUpdating(null)
    }
  }

  const pendingCount = deleteRequests.filter(r => r.status === 'pending').length
  const pendingModerationCount = publicationsForModeration.filter(p => p.moderation_status === 'pending').length

  return (
    <div className="admin-panel">
      <h1>Админ-панель</h1>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'moderation' ? 'active' : ''}`}
          onClick={() => setActiveTab('moderation')}
        >
          <Clock size={18} />
          Модерация публикаций
          {pendingModerationCount > 0 && <span className="badge">{pendingModerationCount}</span>}
        </button>
        <button 
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <Users size={18} />
          Пользователи
        </button>
        <button 
          className={`tab ${activeTab === 'requests' ? 'active' : ''}`}
          onClick={() => setActiveTab('requests')}
        >
          <FileText size={18} />
          Запросы на удаление
          {pendingCount > 0 && <span className="badge">{pendingCount}</span>}
        </button>
        <button 
          className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <Activity size={18} />
          Журнал активности
        </button>
      </div>

      {activeTab === 'moderation' && (
        <div className="tab-content">
          <h2>Очередь модерации</h2>
          {loading ? (
            <div className="loading">Загрузка...</div>
          ) : selectedPub ? (
            // Детальный просмотр публикации для модерации
            <div className="moderation-detail">
              <div className="moderation-header">
                <button className="btn-back" onClick={() => { setSelectedPub(null); setModerationComment('') }}>
                  ← Назад к списку
                </button>
                <span className={`status-badge ${selectedPub.moderation_status}`}>
                  {selectedPub.moderation_status_display || selectedPub.moderation_status}
                </span>
              </div>
              
              <div className="pub-detail-card">
                <h3>{selectedPub.title}</h3>
                <p className="author"><strong>Автор:</strong> {selectedPub.author}</p>
                <div className="pub-meta">
                  <span><strong>Год:</strong> {selectedPub.year}</span>
                  <span><strong>Кафедра:</strong> {selectedPub.department}</span>
                  <span><strong>Владелец:</strong> {selectedPub.owner_username}</span>
                </div>
                <p className="date-info">
                  <span>Создано: {new Date(selectedPub.created_at).toLocaleString()}</span>
                  {selectedPub.updated_at !== selectedPub.created_at && (
                    <span> • Обновлено: {new Date(selectedPub.updated_at).toLocaleString()}</span>
                  )}
                </p>
              </div>
              
              <div className="moderation-form">
                <h4>Решение модератора</h4>
                <div className="form-group full-width">
                  <label>Комментарий (необязательно)</label>
                  <textarea
                    value={moderationComment}
                    onChange={(e) => setModerationComment(e.target.value)}
                    rows={4}
                    placeholder="Укажите причину отклонения или дополнительные комментарии..."
                  />
                </div>
                
                <div className="moderation-actions">
                  <button 
                    className="btn-approve"
                    onClick={() => moderatePublication(selectedPub.id, 'approved')}
                    disabled={updating === selectedPub.id}
                  >
                    <Check size={18} />
                    Одобрить публикацию
                  </button>
                  <button 
                    className="btn-reject"
                    onClick={() => moderatePublication(selectedPub.id, 'rejected')}
                    disabled={updating === selectedPub.id}
                  >
                    <X size={18} />
                    Отклонить публикацию
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="moderation-list">
              {publicationsForModeration.length === 0 ? (
                <p className="empty-message">Нет публикаций на модерации</p>
              ) : (
                <div className="cards-grid">
                  {publicationsForModeration.map(pub => (
                    <div key={pub.id} className={`pub-card moderation-card ${pub.moderation_status}`}>
                      <div className="pub-header">
                        <span className={`status-badge ${pub.moderation_status}`}>
                          {pub.moderation_status_display || pub.moderation_status}
                        </span>
                        <Clock size={16} className="clock-icon" />
                      </div>
                      <h3>{pub.title}</h3>
                      <p className="author">{pub.author}</p>
                      <div className="pub-meta">
                        <span>{pub.year}</span>
                        <span>{pub.department}</span>
                        <span>{pub.owner_username}</span>
                      </div>
                      <p className="date">Создано: {new Date(pub.created_at).toLocaleDateString()}</p>
                      <button 
                        className="btn-view"
                        onClick={() => setSelectedPub(pub)}
                      >
                        <Eye size={16} />
                        Рассмотреть
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'users' && (
        <div className="tab-content">
          <h2>Пользователи системы</h2>
          {loading ? (
            <div className="loading">Загрузка...</div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Логин</th>
                    <th>ФИО</th>
                    <th>Email</th>
                    <th>Роль</th>
                    <th>Записей</th>
                    <th>Статус</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id}>
                      <td>{user.username}</td>
                      <td>{user.first_name} {user.last_name}</td>
                      <td>{user.email}</td>
                      <td>
                        <select 
                          value={user.role}
                          onChange={(e) => updateUserRole(user.id, e.target.value)}
                          disabled={updating === user.id}
                        >
                          <option value="ADMIN">Администратор</option>
                          <option value="METHODIST">Методист кафедры</option>
                          <option value="NIO_STAFF">Сотрудник НИО</option>
                        </select>
                      </td>
                      <td>{user.publications_count}</td>
                      <td>
                        <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Активен' : 'Деактивирован'}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn-toggle"
                          onClick={() => toggleUserActive(user.id, !user.is_active)}
                          disabled={updating === user.id}
                        >
                          {user.is_active ? 'Деактивировать' : 'Активировать'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'requests' && (
        <div className="tab-content">
          <h2>Запросы на удаление</h2>
          {loading ? (
            <div className="loading">Загрузка...</div>
          ) : (
            <div className="requests-list">
              {deleteRequests.map(req => (
                <div key={req.id} className={`request-card ${req.status}`}>
                  <div className="request-header">
                    <span className={`status-badge ${req.status}`}>{req.status_display}</span>
                    <span className="date">{new Date(req.created_at).toLocaleString()}</span>
                  </div>
                  <h3>{req.publication_title}</h3>
                  <p className="requester">Заявитель: {req.requester_username}</p>
                  <p className="reason"><strong>Причина:</strong> {req.reason}</p>
                  
                  {req.status === 'pending' && (
                    <div className="request-actions">
                      <button 
                        className="btn-approve"
                        onClick={() => reviewDeleteRequest(req.id, 'approved')}
                        disabled={updating === req.id}
                      >
                        <Check size={16} />
                        Одобрить
                      </button>
                      <button 
                        className="btn-reject"
                        onClick={() => reviewDeleteRequest(req.id, 'rejected')}
                        disabled={updating === req.id}
                      >
                        <X size={16} />
                        Отклонить
                      </button>
                    </div>
                  )}
                </div>
              ))}
              {deleteRequests.length === 0 && (
                <p className="empty">Нет запросов на удаление</p>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="tab-content">
          <h2>Журнал активности</h2>
          {loading ? (
            <div className="loading">Загрузка...</div>
          ) : (
            <div className="logs-table">
              {logs.map(log => (
                <div key={log.id} className="log-row">
                  <span className="log-time">{new Date(log.timestamp).toLocaleString()}</span>
                  <span className="log-action">{log.action_display}</span>
                  <span className="log-user">{log.user_username || 'Система'}</span>
                  <span className="log-details">{log.publication_title || '-'}</span>
                  <span className="log-ip">{log.ip_address || '-'}</span>
                </div>
              ))}
              {logs.length === 0 && (
                <p className="empty">Нет записей в журнале</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AdminPanel