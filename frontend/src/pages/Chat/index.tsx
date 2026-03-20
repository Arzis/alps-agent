import React, { useState, useEffect } from 'react';
import { Layout } from 'antd';
import { useChatStore } from '@/stores/chatStore';
import SessionList from './SessionList';
import ChatWindow from './ChatWindow';
import CitationPanel from './CitationPanel';

const { Sider, Content } = Layout;

const ChatPage: React.FC = () => {
  const [citationPanelOpen, setCitationPanelOpen] = useState(true);
  const { activeSessionId } = useChatStore();

  return (
    <Layout className="h-full">
      {/* 左侧: 会话列表 */}
      <Sider
        width={280}
        className="bg-white border-r overflow-y-auto"
      >
        <SessionList />
      </Sider>

      {/* 中间: 对话窗口 */}
      <Content className="flex flex-col bg-gray-50">
        <ChatWindow
          sessionId={activeSessionId}
          onCitationClick={() => setCitationPanelOpen(true)}
        />
      </Content>

      {/* 右侧: 引用/详情面板 */}
      {citationPanelOpen && activeSessionId && (
        <Sider
          width={320}
          className="bg-gray-50 border-l overflow-y-auto"
        >
          <CitationPanel
            sessionId={activeSessionId}
            onClose={() => setCitationPanelOpen(false)}
          />
        </Sider>
      )}
    </Layout>
  );
};

export default ChatPage;
