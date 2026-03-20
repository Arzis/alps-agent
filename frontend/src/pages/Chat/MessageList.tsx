import React from 'react';
import type { ChatMessage } from '@/types/chat';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onCitationClick?: () => void;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  isStreaming,
  onCitationClick,
}) => {
  return (
    <div className="space-y-4">
      {messages.map((msg, index) => (
        <MessageBubble
          key={msg.id || index}
          message={msg}
          isStreaming={isStreaming && index === messages.length - 1}
          onCitationClick={onCitationClick}
        />
      ))}
    </div>
  );
};

export default MessageList;
