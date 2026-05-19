import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login/Login'
import PublicWorks from './pages/PublicWorks/PublicWorks'
import Statistics from './pages/Statistics/Statistics'
import AdminPanel from './pages/AdminPanel/AdminPanel'
import MethodistCabinet from './pages/MethodistCabinet/MethodistCabinet'
import Layout from './components/Layout/Layout'
import ToastProvider from './Toast'

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth()
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/public-works" replace />} />
          <Route path="public-works" element={<PublicWorks />} />
          <Route path="statistics" element={<Statistics />} />
          <Route 
            path="admin" 
            element={
              <ProtectedRoute>
                <AdminPanel />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="cabinet" 
            element={
              <ProtectedRoute>
                <MethodistCabinet />
              </ProtectedRoute>
            } 
          />
        </Route>
      </Routes>
    </ToastProvider>
  )
}

export default App
