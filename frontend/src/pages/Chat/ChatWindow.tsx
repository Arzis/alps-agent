import React, { useRef, useEffect, useState } from 'react';
import { Button, Select, Space, Tag, message } from 'antd';
import { SendOutlined, StopOutlined } from '@ant-design/icons';
import { useChat } from '@/hooks/useChat';
import { useChatStore } from '@/stores/chatStore';
import MessageList from './MessageList';
import InputArea from './InputArea';
import EmptyState from '@/components/common/EmptyState';

interface ChatWindowProps {
  sessionId: string | null;
  onCitationClick: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  sessionId,
  onCitationClick,
}) => {
  const [collection, setCollection] = useState('default');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isStreaming, sessionStatus, sendMessage, stopStreaming } =
    useChat({ sessionId });

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (content: string) => {
    if (!content.trim()) return;
    try {
      await sendMessage(content);
    } catch (error) {
      message.error('发送失败，请重试');
    }
  };

  const collections = [
    { label: '全部知识库', value: 'default' },
    { label: 'HR制度文档', value: 'hr_docs' },
    { label: '产品手册', value: 'product_docs' },
    { label: '技术文档', value: 'tech_docs' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* 顶栏: 知识库选择 */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-white">
        <Space>
          <span className="text-gray-500">知识库:</span>
          <Select
            value={collection}
            onChange={setCollection}
            style={{ width: 200 }}
            options={collections}
          />
        </Space>
        {isStreaming && (
          <Button
            size="small"
            danger
            icon={<StopOutlined />}
            onClick={stopStreaming}
          >
            停止生成
          </Button>
        )}
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <EmptyState
            type="chat"
            title="开始新对话"
            description="输入您的问题，AI 助手将基于知识库内容为您解答"
          />
        ) : (
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            onCitationClick={onCitationClick}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <InputArea
        onSend={handleSend}
        disabled={isStreaming || sessionStatus === 'waiting_review'}
        isStreaming={isStreaming}
      />
    </div>
  );
};

export default ChatWindow;
