import React from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { BookOpen, LogOut, User, BarChart3, Settings } from 'lucide-react'
import './Layout.css'

const Layout: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to="/" className="logo">
            <BookOpen size={24} />
            <span>База научных трудов</span>
          </Link>
          
          <nav className="nav">
            <Link 
              to="/" 
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            >
              Публикации
            </Link>
            
            {user ? (
              <>
                <Link 
                  to="/cabinet" 
                  className={`nav-link ${location.pathname === '/cabinet' ? 'active' : ''}`}
                >
                  Кабинет
                </Link>
                <Link 
                  to="/statistics" 
                  className={`nav-link ${location.pathname === '/statistics' ? 'active' : ''}`}
                >
                  <BarChart3 size={16} />
                  Статистика
                </Link>
                {user.role === 'ADMIN' && (
                  <Link 
                    to="/admin" 
                    className={`nav-link ${location.pathname === '/admin' ? 'active' : ''}`}
                  >
                    Админ-панель
                  </Link>
                )}
                <div className="user-menu">
                  <span className="user-info">
                    <User size={16} />
                    {user.first_name} {user.last_name}
                  </span>
                  <button onClick={handleLogout} className="btn-logout">
                    <LogOut size={16} />
                    Выход
                  </button>
                </div>
              </>
            ) : (
              <Link to="/login" className="btn-login">
                <Settings size={16} />
                Вход
              </Link>
            )}
          </nav>
        </div>
      </header>
      
      <main className="main">
        <Outlet />
      </main>
      
      <footer className="footer">
        <p>База научных трудов © 2024</p>
      </footer>
    </div>
  )
}

export default Layout