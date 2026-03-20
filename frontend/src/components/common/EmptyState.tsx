import React from 'react';
import { Button } from 'antd';
import { FileTextOutlined, MessageOutlined, UploadOutlined } from '@ant-design/icons';

interface EmptyStateProps {
  type?: 'default' | 'chat' | 'documents' | 'search';
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

const defaultContent: Record<
  string,
  { title: string; description: string; icon: React.ReactNode }
> = {
  chat: {
    title: '开始新对话',
    description: '输入您的问题，AI 助手将为您解答',
    icon: <MessageOutlined className="text-4xl text-gray-400" />,
  },
  documents: {
    title: '暂无文档',
    description: '上传文档以开始构建知识库',
    icon: <FileTextOutlined className="text-4xl text-gray-400" />,
  },
  search: {
    title: '未找到结果',
    description: '尝试更换搜索关键词',
    icon: <MessageOutlined className="text-4xl text-gray-400" />,
  },
  default: {
    title: '暂无数据',
    description: '',
    icon: null,
  },
};

const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'default',
  title,
  description,
  actionText,
  onAction,
}) => {
  const content = defaultContent[type];

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {content.icon && <div className="mb-4">{content.icon}</div>}
      <h3 className="text-lg font-medium text-gray-700 mb-1">
        {title || content.title}
      </h3>
      <p className="text-sm text-gray-500 mb-4 text-center max-w-sm">
        {description || content.description}
      </p>
      {actionText && onAction && (
        <Button type="primary" onClick={onAction} icon={<UploadOutlined />}>
          {actionText}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
