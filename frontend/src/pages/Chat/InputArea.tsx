import React, { useState, useRef, KeyboardEvent } from 'react';
import { Button, Input } from 'antd';
import {
  SendOutlined,
  StopOutlined,
  PaperClipOutlined,
} from '@ant-design/icons';

const { TextArea } = Input;

interface InputAreaProps {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
  isStreaming?: boolean;
}

const InputArea: React.FC<InputAreaProps> = ({
  onSend,
  disabled = false,
  isStreaming = false,
}) => {
  const [value, setValue] = useState('');
  const [sending, setSending] = useState(false);
  const textareaRef = useRef<TextArea>(null);

  const handleSend = async () => {
    if (!value.trim() || disabled || sending) return;

    const content = value.trim();
    setValue('');
    setSending(true);

    try {
      await onSend(content);
    } finally {
      setSending(false);
    }

    // 聚焦回输入框
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter 或 Cmd+Enter 发送
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t bg-white p-4">
      <div className="flex items-end gap-2">
        <TextArea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入您的问题... (Ctrl+Enter 发送)"
          autoSize={{ minRows: 1, maxRows: 6 }}
          disabled={disabled}
          className="flex-1"
        />
        <div className="flex gap-2">
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            loading={sending}
          >
            发送
          </Button>
        </div>
      </div>
      <div className="mt-2 text-xs text-gray-400">
        按 Ctrl+Enter 快速发送
      </div>
    </div>
  );
};

export default InputArea;
