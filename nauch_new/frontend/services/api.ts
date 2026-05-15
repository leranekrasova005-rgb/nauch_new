import axios, { AxiosError } from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

console.log('API baseURL:', api.defaults.baseURL)

// Интерфейс для расширенной ошибки валидации
export interface ValidationError {
  field?: string
  message: string
  code?: string
}

export interface ApiError {
  detail?: string
  non_field_errors?: string[]
  [key: string]: any
}

api.interceptors.request.use((config) => {
  console.log('Request:', config.method, config.url)
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Добавляем заголовок для JSON
  config.headers['Content-Type'] = 'application/json'
  return config
})

api.interceptors.response.use(
  (response) => {
    console.log('Response:', response.status, response.config.url)
    return response
  },
  async (error: AxiosError<ApiError>) => {
    console.error('Response error:', error.response?.status, error.response?.data)
    const originalRequest = error.config
    
    // Обработка 401 - токены
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refresh = localStorage.getItem('refresh_token')
        const res = await axios.post(`${api.defaults.baseURL}/users/auth/refresh/`, { refresh })
        const { access } = res.data
        
        localStorage.setItem('access_token', access)
        originalRequest.headers.Authorization = `Bearer ${access}`
        
        return api(originalRequest)
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    
    // Пробрасываем ошибку дальше для обработки в компонентах
    return Promise.reject(error)
  }
)

// Helper для парсинга ошибок валидации
export const parseValidationErrors = (error: AxiosError<ApiError>): Record<string, string> => {
  const errors: Record<string, string> = {}
  const data = error.response?.data
  
  if (!data) {
    return { general: 'Неизвестная ошибка сервера' }
  }
  
  // non_field_errors
  if (Array.isArray(data.non_field_errors)) {
    errors.general = data.non_field_errors.join('. ')
  }
  
  // Полевые ошибки
  Object.keys(data).forEach(key => {
    if (key !== 'non_field_errors' && key !== 'detail') {
      const value = data[key]
      if (Array.isArray(value)) {
        errors[key] = value.join('. ')
      } else if (typeof value === 'string') {
        errors[key] = value
      }
    }
  })
  
  // Fallback на detail
  if (Object.keys(errors).length === 0 && data.detail) {
    errors.general = data.detail
  }
  
  return errors
}

export default api
