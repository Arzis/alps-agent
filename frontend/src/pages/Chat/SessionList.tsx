import React, { useEffect, useState } from 'react';
import { Input, Button, List, Skeleton, message } from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import { useChatStore } from '@/stores/chatStore';
import { getSessions, deleteSession } from '@/services/chatService';
import type { SessionInfo } from '@/types/chat';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const SessionList: React.FC = () => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const {
    activeSessionId,
    setActiveSession,
    removeSession,
  } = useChatStore();

  const loadSessions = async () => {
    try {
      setLoading(true);
      const data = await getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteSession(sessionId);
      removeSession(sessionId);
      if (activeSessionId === sessionId) {
        setActiveSession(null);
      }
      message.success('会话已删除');
      loadSessions();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleNewChat = () => {
    setActiveSession(null);
  };

  const filteredSessions = sessions.filter((session) =>
    session.title.toLowerCase().includes(searchText.toLowerCase())
  );

  const renderSessionItem = (session: SessionInfo) => (
    <div
      key={session.session_id}
      className={`p-3 cursor-pointer hover:bg-gray-100 rounded-lg transition-colors ${
        activeSessionId === session.session_id ? 'bg-blue-50 border border-blue-200' : ''
      }`}
      onClick={() => setActiveSession(session.session_id)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <MessageOutlined className="text-gray-400 flex-shrink-0" />
            <span className="font-medium text-gray-800 truncate">
              {session.title || '新对话'}
            </span>
          </div>
          <div className="flex items-center justify-between mt-1 text-xs text-gray-500">
            <span>{dayjs(session.updated_at).fromNow()}</span>
            <span>{session.message_count} 条消息</span>
          </div>
        </div>
        <Button
          type="text"
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={(e) => handleDeleteSession(session.session_id, e)}
          className="opacity-0 group-hover:opacity-100"
        />
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col p-3">
      {/* 搜索 */}
      <Input
        prefix={<SearchOutlined className="text-gray-400" />}
        placeholder="搜索会话..."
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        className="mb-3"
      />

      {/* 新对话按钮 */}
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={handleNewChat}
        className="mb-3 w-full"
      >
        新对话
      </Button>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto -mx-3 px-3">
        {loading ? (
          <Skeleton active />
        ) : filteredSessions.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            {searchText ? '未找到匹配的会话' : '暂无会话记录'}
          </div>
        ) : (
          <List
            dataSource={filteredSessions}
            renderItem={renderSessionItem}
            split={false}
          />
        )}
      </div>
    </div>
  );
};

export default SessionList;
