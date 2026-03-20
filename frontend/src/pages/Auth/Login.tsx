import { useState } from 'react'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

const { Title, Text } = Typography

interface LoginForm {
  username: string
  password: string
}

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)

  const onFinish = async (values: LoginForm) => {
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('username', values.username)
      formData.append('password', values.password)

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '登录失败')
      }

      const data = await response.json()

      // 获取用户信息
      const userResponse = await fetch('/api/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      })

      if (!userResponse.ok) {
        throw new Error('获取用户信息失败')
      }

      const userData = await userResponse.json()

      // 存储认证信息
      login(userData, data.access_token)

      message.success('登录成功')
      navigate('/chat')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3}>企业智能问答助手</Title>
          <Text type="secondary">用户登录</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">还没有账号？</Text>
            <Button type="link" size="small" onClick={() => navigate('/register')}>
              注册账号
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  )
}
