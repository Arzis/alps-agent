import React, { useEffect, useState } from 'react';
import { Card, Tag, Progress, Skeleton, Button, Empty } from 'antd';
import { CloseOutlined, FileTextOutlined } from '@ant-design/icons';
import { getConversationHistory } from '@/services/chatService';
import type { ChatMessage, Citation } from '@/types/chat';

interface CitationPanelProps {
  sessionId: string;
  onClose: () => void;
}

const CitationPanel: React.FC<CitationPanelProps> = ({
  sessionId,
  onClose,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await getConversationHistory(sessionId);
        setMessages(history.messages);
      } catch (error) {
        console.error('Failed to load history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, [sessionId]);

  // 获取所有引用
  const allCitations: Citation[] = [];
  messages.forEach((msg) => {
    if (msg.metadata?.citations) {
      allCitations.push(...msg.metadata.citations);
    }
  });

  const renderCitationItem = (citation: Citation, index: number) => (
    <Card
      key={`${citation.doc_id}-${index}`}
      id={`citation-${index + 1}`}
      size="small"
      className="mb-3 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start gap-2">
        <FileTextOutlined className="text-blue-500 mt-1 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="font-medium text-gray-800 truncate">
              {citation.doc_title}
            </span>
            <Tag color="blue">
              相关度 {Math.round(citation.relevance_score * 100)}%
            </Tag>
          </div>
          <p className="text-sm text-gray-600 line-clamp-3">
            {citation.content}
          </p>
        </div>
      </div>
    </Card>
  );

  return (
    <div className="h-full flex flex-col p-4">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-lg">引用来源</h3>
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          onClick={onClose}
        />
      </div>

      {/* 引用列表 */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <Skeleton active />
        ) : allCitations.length === 0 ? (
          <Empty
            description="暂无引用来源"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          allCitations.map((citation, index) =>
            renderCitationItem(citation, index)
          )
        )}
      </div>
    </div>
  );
};

export default CitationPanel;
