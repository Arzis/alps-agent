import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import MainLayout from './layouts/MainLayout'
import ChatLayout from './layouts/ChatLayout'
import Loading from './components/common/Loading'
import { useAuthStore } from './stores/authStore'

// 懒加载页面组件
const ChatPage = lazy(() => import('./pages/Chat'))
const DocumentsPage = lazy(() => import('./pages/Documents'))
const EvaluationPage = lazy(() => import('./pages/Evaluation'))
const MonitoringPage = lazy(() => import('./pages/Monitoring'))
const LoginPage = lazy(() => import('./pages/Auth/Login'))
const RegisterPage = lazy(() => import('./pages/Auth/Register'))

// 路由守卫组件
function AuthRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to='/login' replace />
  }

  return <>{children}</>
}

// 公开路由守卫 (已登录用户访问登录页则跳转到 chat)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (isAuthenticated) {
    return <Navigate to='/chat' replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        {/* 公开路由 - 登录/注册 */}
        <Route
          path='/login'
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path='/register'
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />

        {/* 受保护的 Chat 页面使用独立的 ChatLayout */}
        <Route
          element={
            <AuthRoute>
              <ChatLayout />
            </AuthRoute>
          }
        >
          <Route path='/chat' element={<ChatPage />} />
        </Route>

        {/* 其他页面使用 MainLayout */}
        <Route
          element={
            <AuthRoute>
              <MainLayout />
            </AuthRoute>
          }
        >
          <Route path='/documents' element={<DocumentsPage />} />
          <Route path='/evaluation' element={<EvaluationPage />} />
          <Route path='/monitoring' element={<MonitoringPage />} />
        </Route>

        {/* 默认重定向 */}
        <Route path='/' element={<Navigate to='/chat' replace />} />
        <Route path='*' element={<Navigate to='/chat' replace />} />
      </Routes>
    </Suspense>
  )
}

export default App
