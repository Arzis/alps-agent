# 企业智能问答助手 - 前端

## 技术栈

- **框架**: React 18.3 + TypeScript 5.4
- **构建工具**: Vite 5.x
- **UI 组件库**: Ant Design 5.x
- **样式**: TailwindCSS 3.x + CSS Modules
- **状态管理**: Zustand 4.x
- **服务端状态**: TanStack React Query 5.x
- **路由**: React Router 6.x
- **图表**: ECharts 5.x
- **Markdown**: react-markdown + rehype-highlight

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── config/               # 配置
│   │   ├── routes.tsx        # 路由配置
│   │   ├── theme.ts          # 主题配置
│   │   └── api.ts            # API 端点
│   ├── layouts/               # 布局组件
│   ├── pages/                 # 页面组件
│   │   ├── Chat/             # 对话页面
│   │   ├── Documents/        # 文档管理
│   │   ├── Evaluation/        # 评估中心
│   │   └── Monitoring/        # 系统监控
│   ├── components/            # 公共组件
│   │   ├── common/           # 通用组件
│   │   └── charts/           # 图表组件
│   ├── hooks/                # 自定义 Hooks
│   ├── stores/                # Zustand 状态
│   ├── services/              # API 服务层
│   └── types/                 # TypeScript 类型
├── index.html
├── package.json
└── vite.config.ts
```

## 页面路由

| 路径 | 页面 | 描述 |
|------|------|------|
| `/chat` | 对话页面 | 核心问答界面，支持 SSE 流式对话 |
| `/documents` | 文档管理 | 上传和管理知识库文档 |
| `/evaluation` | 评估中心 | RAG 质量评估和趋势分析 |
| `/monitoring` | 系统监控 | 系统运行状态和性能指标 |

## 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `VITE_API_BASE` | 空 | API 基础 URL（为空时使用 Vite 代理） |

## API 代理配置

开发环境下，Vite 会将 `/api` 和 `/health` 请求代理到 `http://localhost:8000`。

确保后端服务运行在 localhost:8000。

## 代码规范

```bash
# 格式化
npm run format

# 类型检查
npm run typecheck

# ESLint
npm run lint
```

## 开发指南

### 添加新页面

1. 在 `src/pages/` 下创建页面组件
2. 在 `src/config/routes.tsx` 中添加路由
3. 配置对应的 Layout（MainLayout 或 ChatLayout）

### 添加 API

1. 在 `src/types/` 中定义类型
2. 在 `src/services/` 中创建服务函数
3. 使用 React Query 进行数据获取

### 添加组件

1. 通用组件放在 `src/components/common/`
2. 业务组件放在 `src/components/business/`
3. 图表组件放在 `src/components/charts/`
