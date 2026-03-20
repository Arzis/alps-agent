import React, { useState } from 'react';
import { Avatar, Tag, Tooltip, Space, Button, message } from 'antd';
import {
  RobotOutlined,
  UserOutlined,
  LikeOutlined,
  DislikeOutlined,
  LikeFilled,
  DislikeFilled,
  CopyOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import MarkdownRenderer from '@/components/common/MarkdownRenderer';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import type { ChatMessage, Citation } from '@/types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  onCitationClick?: (citations: Citation[]) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message: msg,
  isStreaming = false,
  onCitationClick,
}) => {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const isUser = msg.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    message.success('已复制到剪贴板');
  };

  const handleFeedback = (type: 'thumbs_up' | 'thumbs_down') => {
    setFeedback(type === 'thumbs_up' ? 'up' : 'down');
    message.success('感谢您的反馈!');
  };

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* 头像 */}
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        className={isUser ? 'bg-blue-500' : 'bg-green-500 flex-shrink-0'}
      />

      {/* 消息内容 */}
      <div
        className={`max-w-[70%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}
      >
        {/* 消息气泡 */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-blue-500 text-white rounded-tr-sm'
              : 'bg-white border border-gray-200 rounded-tl-sm shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <MarkdownRenderer content={msg.content} />
          )}
          {isStreaming && (
            <span className="inline-block ml-1 animate-pulse">▌</span>
          )}
        </div>

        {/* 助手消息的元数据 */}
        {!isUser && msg.metadata && (
          <div className="mt-2 flex flex-col gap-2">
            {/* 引用 + 置信度 */}
            <Space size={8} wrap>
              {msg.metadata.confidence !== undefined && (
                <ConfidenceBadge value={msg.metadata.confidence} />
              )}
              {msg.metadata.model_used && (
                <Tag color="blue">{msg.metadata.model_used}</Tag>
              )}
              {msg.metadata.fallback_used && (
                <Tag color="orange">降级回答</Tag>
              )}
              {msg.metadata.cache_hit && (
                <Tag color="green">缓存命中</Tag>
              )}
              {msg.metadata.citations && msg.metadata.citations.length > 0 && (
                <Button
                  type="link"
                  size="small"
                  onClick={() =>
                    onCitationClick?.(msg.metadata?.citations || [])
                  }
                >
                  📎 {msg.metadata.citations.length} 个引用来源
                </Button>
              )}
            </Space>

            {/* 操作按钮 */}
            <Space size={4}>
              <Tooltip title="有帮助">
                <Button
                  type="text"
                  size="small"
                  icon={
                    feedback === 'up' ? (
                      <LikeFilled className="text-green-500" />
                    ) : (
                      <LikeOutlined />
                    )
                  }
                  onClick={() => handleFeedback('thumbs_up')}
                />
              </Tooltip>
              <Tooltip title="没有帮助">
                <Button
                  type="text"
                  size="small"
                  icon={
                    feedback === 'down' ? (
                      <DislikeFilled className="text-red-500" />
                    ) : (
                      <DislikeOutlined />
                    )
                  }
                  onClick={() => handleFeedback('thumbs_down')}
                />
              </Tooltip>
              <Tooltip title="复制">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={handleCopy}
                />
              </Tooltip>
            </Space>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
