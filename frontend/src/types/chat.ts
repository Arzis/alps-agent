// 对话相关类型定义

export interface ChatMessage {
  id: string | number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    confidence?: number;
    model_used?: string;
    fallback_used?: boolean;
    cache_hit?: boolean;
    latency_ms?: number;
    tokens_used?: number;
    agent_used?: string;
    citations?: Citation[];
    [key: string]: unknown;
  };
}

export interface Citation {
  doc_id: string;
  doc_title: string;
  content: string;
  chunk_index: number;
  relevance_score: number;
}

export interface SessionInfo {
  session_id: string;
  title: string;
  message_count: number;
  status: 'active' | 'waiting_review' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface ConversationHistory {
  session_id: string;
  messages: ChatMessage[];
  total_count: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  collection?: string;
  stream?: boolean;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  citations: Citation[];
  confidence: number;
  model_used: string;
  fallback_used: boolean;
  latency_ms: number;
  tokens_used: number;
}

export type SessionStatus = 'active' | 'waiting_review' | 'completed';

// SSE 事件类型
export interface StreamEvent {
  event: 'token' | 'citation' | 'status' | 'done' | 'error';
  data: string;
}
