import React, { useState } from 'react'
import { Layout, Menu, theme, Dropdown, Button, Space } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
  DashboardOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '@/stores/authStore'

const { Header, Sider, Content } = Layout

const menuItems: MenuProps['items'] = [
  {
    key: '/chat',
    icon: <MessageOutlined />,
    label: '智能问答',
  },
  {
    key: '/documents',
    icon: <FileTextOutlined />,
    label: '文档管理',
  },
  {
    key: '/evaluation',
    icon: <BarChartOutlined />,
    label: '评估中心',
  },
  {
    key: '/monitoring',
    icon: <DashboardOutlined />,
    label: '系统监控',
  },
]

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const { user, logout } = useAuthStore()

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout className='min-h-screen'>
      <Sider trigger={null} collapsible collapsed={collapsed} width={220} className='shadow-md'>
        <div className='h-14 flex items-center justify-center border-b border-gray-200'>
          <span className='text-lg font-semibold text-primary-600'>
            {collapsed ? 'QA' : '智能问答助手'}
          </span>
        </div>
        <Menu
          mode='inline'
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className='mt-2'
        />
      </Sider>
      <Layout>
        <Header className='px-4 flex items-center justify-between shadow-sm'>
          <div className='text-sm text-gray-500'>企业智能问答助手 v1.0.0</div>
          <div className='flex items-center gap-2'>
            <Dropdown menu={{ items: userMenuItems }} placement='bottomRight'>
              <Button type='text' icon={<UserOutlined />}>
                <Space>
                  <span className='text-sm'>{user?.username || '用户'}</span>
                </Space>
              </Button>
            </Dropdown>
          </div>
        </Header>
        <Content className='m-4 p-6 rounded-lg' style={{ background: colorBgContainer }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
