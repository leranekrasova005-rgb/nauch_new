import { useState, useEffect } from 'react'
import api from '../../services/api'
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import './PublicWorks.css'

interface Publication {
  id: number
  title: string
  author: string
  year: number
  department: string
  department_display: string
  result: string
  status: string
  status_display: string
  owner_username: string
  created_at: string
}

const DEPARTMENTS = [
  { value: '', label: 'Все кафедры' },
  { value: 'КТОиТК', label: 'Кафедра таможенных операций и таможенного контроля' },
  { value: 'КТиТЭ', label: 'Кафедра товароведения и таможенной экспертизы' },
  { value: 'КУиЭТД', label: 'Кафедра управления и экономики таможенного дела' },
  { value: 'КЭТиМЭО', label: 'Кафедра экономической теории и международных экономических отношений' },
  { value: 'КГПД', label: 'Кафедра государственно-правовых дисциплин' },
  { value: 'КГрПД', label: 'Кафедра гражданско-правовых дисциплин' },
  { value: 'КУПД', label: 'Кафедра уголовно-правовых дисциплин' },
  { value: 'КГД', label: 'Кафедра гуманитарных дисциплин' },
  { value: 'КИЯ', label: 'Кафедра иностранных языков' },
  { value: 'КИиИТТ', label: 'Кафедра информатики и информационных таможенных технологий' },
  { value: 'КФП', label: 'Кафедра физической подготовки' },
]

const YEARS = [
  { value: '', label: 'Все годы' },
  { value: '2024', label: '2024' },
  { value: '2023', label: '2023' },
  { value: '2022', label: '2022' },
  { value: '2021', label: '2021' },
  { value: '2020', label: '2020' },
]

const RESULTS = [
  { value: '', label: 'Все результаты' },
  { value: 'победитель', label: 'Победитель' },
  { value: 'призёр', label: 'Призёр' },
  { value: 'участник', label: 'Участник' },
]

const PublicWorks: React.FC = () => {
  const [publications, setPublications] = useState<Publication[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [department, setDepartment] = useState('')
  const [year, setYear] = useState('')
  const [result, setResult] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    loadPublications()
  }, [search, department, year, result, page])

  const loadPublications = async () => {
    try {
      const params = new URLSearchParams()
      params.append('page', page.toString())
      if (search) params.append('search', search)
      if (department) params.append('department', department)
      if (year) params.append('year', year)
      if (result) params.append('result', result)
      
      const response = await api.get(`/publications/?${params}`)
      const data = response.data
      setPublications(data.results || data)
      setTotalPages(Math.ceil((data.count || 0) / 20))
    } catch (error) {
      console.error('Error loading publications:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="public-works">
      <div className="page-header">
        <h1>Публикации и мероприятия</h1>
        <p className="subtitle">База научных трудов и достижений</p>
      </div>

      <div className="filters">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Поиск по названию, автору..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        <div className="filter-group">
          <Filter size={20} />
          <select value={department} onChange={(e) => { setDepartment(e.target.value); setPage(1); }}>
            {DEPARTMENTS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
          </select>

          <select value={year} onChange={(e) => { setYear(e.target.value); setPage(1); }}>
            {YEARS.map(y => <option key={y.value} value={y.value}>{y.label}</option>)}
          </select>

          <select value={result} onChange={(e) => { setResult(e.target.value); setPage(1); }}>
            {RESULTS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th>Автор</th>
                  <th>Год</th>
                  <th>Кафедра</th>
                  <th>Результат</th>
                </tr>
              </thead>
              <tbody>
                {publications.map(pub => (
                  <tr key={pub.id}>
                    <td className="title-cell">{pub.title}</td>
                    <td>{pub.author}</td>
                    <td>{pub.year}</td>
                    <td>{pub.department_display}</td>
                    <td>
                      <span className={`result-badge ${pub.result}`}>
                        {pub.result === 'победитель' ? '🏆' : pub.result === 'призёр' ? '🥈' : ''} {pub.result || '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                <ChevronLeft size={20} />
              </button>
              <span>Страница {page} из {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                <ChevronRight size={20} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default PublicWorks