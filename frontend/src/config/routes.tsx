import { lazy, ReactNode } from 'react'
import {
  MessageOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  DashboardOutlined,
} from '@ant-design/icons'

export interface RouteConfig {
  path: string
  name: string
  icon?: ReactNode
  component: React.LazyExoticComponent<() => JSX.Element>
  layout?: 'main' | 'chat' | 'none'
  roles?: string[]
  hideInMenu?: boolean
  children?: RouteConfig[]
}

// 页面组件使用懒加载
const ChatPage = lazy(() => import('@/pages/Chat'))
const DocumentsPage = lazy(() => import('@/pages/Documents'))
const EvaluationPage = lazy(() => import('@/pages/Evaluation'))
const MonitoringPage = lazy(() => import('@/pages/Monitoring'))
const LoginPage = lazy(() => import('@/pages/Auth/Login'))
const RegisterPage = lazy(() => import('@/pages/Auth/Register'))

const routes: RouteConfig[] = [
  {
    path: '/login',
    name: '登录',
    component: LoginPage,
    layout: 'none',
    hideInMenu: true,
  },
  {
    path: '/register',
    name: '注册',
    component: RegisterPage,
    layout: 'none',
    hideInMenu: true,
  },
  {
    path: '/chat',
    name: '智能问答',
    icon: <MessageOutlined />,
    component: ChatPage,
    layout: 'chat',
  },
  {
    path: '/documents',
    name: '文档管理',
    icon: <FileTextOutlined />,
    component: DocumentsPage,
    layout: 'main',
  },
  {
    path: '/evaluation',
    name: '评估中心',
    icon: <BarChartOutlined />,
    component: EvaluationPage,
    layout: 'main',
    roles: ['admin'],
  },
  {
    path: '/monitoring',
    name: '系统监控',
    icon: <DashboardOutlined />,
    component: MonitoringPage,
    layout: 'main',
    roles: ['admin'],
  },
]

export default routes
