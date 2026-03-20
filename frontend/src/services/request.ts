import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosError,
} from 'axios';
import { message, notification } from 'antd';
import { useAuthStore } from '@/stores/authStore';

const request: AxiosInstance = axios.create({
  baseURL: '',
  timeout: 120000, // 2分钟 (LLM调用可能较慢)
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加请求ID (用于追踪)
    config.headers['X-Request-ID'] = crypto.randomUUID().slice(0, 8);

    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
request.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error: { code: string; message: string } }>) => {
    const { response } = error;

    if (!response) {
      message.error('网络连接失败, 请检查网络');
      return Promise.reject(error);
    }

    const { status, data } = response;
    const errorMessage = data?.error?.message || '请求失败';

    switch (status) {
      case 401:
        useAuthStore.getState().logout();
        window.location.href = '/login';
        break;

      case 403:
        notification.error({
          message: '权限不足',
          description: errorMessage,
        });
        break;

      case 429:
        notification.warning({
          message: '请求过于频繁',
          description: '请稍后再试',
        });
        break;

      case 502:
        notification.error({
          message: 'AI服务暂时不可用',
          description: '请稍后重试, 或联系管理员',
        });
        break;

      default:
        message.error(errorMessage);
    }

    return Promise.reject(error);
  }
);

export default request;
