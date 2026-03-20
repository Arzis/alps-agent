import { create } from 'zustand';
import type {
  ChatMessage,
  SessionInfo,
  Citation,
  SessionStatus,
} from '@/types/chat';

interface ChatState {
  // 会话
  sessions: SessionInfo[];
  activeSessionId: string | null;

  // 消息
  messages: ChatMessage[];

  // 会话状态
  sessionStatus: SessionStatus;

  // Actions
  setActiveSession: (id: string | null) => void;
  setSessions: (sessions: SessionInfo[]) => void;
  addSession: (session: SessionInfo) => void;
  updateSession: (id: string, updates: Partial<SessionInfo>) => void;
  removeSession: (id: string) => void;

  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  updateLastMessage: (
    updater: (prev: ChatMessage) => ChatMessage
  ) => void;
  updateMessage: (id: string | number, updates: Partial<ChatMessage>) => void;

  setSessionStatus: (status: SessionStatus) => void;

  reset: () => void;
}

const initialState = {
  sessions: [],
  activeSessionId: null,
  messages: [],
  sessionStatus: 'active' as SessionStatus,
};

export const useChatStore = create<ChatState>((set, get) => ({
  ...initialState,

  setActiveSession: (id) =>
    set({
      activeSessionId: id,
      messages: [],
      sessionStatus: 'active',
    }),

  setSessions: (sessions) => set({ sessions }),

  addSession: (session) =>
    set((s) => ({
      sessions: [session, ...s.sessions],
    })),

  updateSession: (id, updates) =>
    set((s) => ({
      sessions: s.sessions.map((session) =>
        session.session_id === id
          ? { ...session, ...updates }
          : session
      ),
    })),

  removeSession: (id) =>
    set((s) => ({
      sessions: s.sessions.filter((session) => session.session_id !== id),
      activeSessionId:
        s.activeSessionId === id ? null : s.activeSessionId,
    })),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((s) => ({
      messages: [...s.messages, message],
    })),

  updateLastMessage: (updater) =>
    set((s) => {
      const msgs = [...s.messages];
      if (msgs.length > 0) {
        msgs[msgs.length - 1] = updater(msgs[msgs.length - 1]);
      }
      return { messages: msgs };
    }),

  updateMessage: (id, updates) =>
    set((s) => ({
      messages: s.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),

  setSessionStatus: (status) => set({ sessionStatus: status }),

  reset: () => set(initialState),
}));

// 辅助函数：创建用户消息
export function createUserMessage(
  content: string
): ChatMessage {
  return {
    id: `user_${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date().toISOString(),
  };
}

// 辅助函数：创建助手消息
export function createAssistantMessage(
  content: string = '',
  metadata: ChatMessage['metadata'] = {}
): ChatMessage {
  return {
    id: `assistant_${Date.now()}`,
    role: 'assistant',
    content,
    timestamp: new Date().toISOString(),
    metadata,
  };
}
