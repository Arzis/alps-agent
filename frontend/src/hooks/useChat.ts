import { useState, useCallback, useRef, useEffect } from 'react'
import { message } from 'antd'
import { useChatStore, createUserMessage, createAssistantMessage } from '@/stores/chatStore'
import { getConversationHistory, createStreamRequest } from '@/services/chatService'
import type { ChatMessage, Citation, ChatRequest } from '@/types/chat'

interface UseChatOptions {
  sessionId: string | null
  collection?: string
}

interface UseChatReturn {
  messages: ChatMessage[]
  isStreaming: boolean
  sessionStatus: 'active' | 'waiting_review' | 'completed'
  sendMessage: (content: string) => Promise<void>
  stopStreaming: () => void
  loadHistory: () => Promise<void>
}

export function useChat({ sessionId, collection = 'default' }: UseChatOptions): UseChatReturn {
  const {
    messages,
    setMessages,
    addMessage,
    updateLastMessage,
    sessionStatus,
    setSessionStatus,
    setActiveSession,
  } = useChatStore()

  const [isStreaming, setIsStreaming] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  // 追踪是否是新会话（发送新消息时避免加载历史覆盖）
  const isNewSessionRef = useRef(false)

  // 加载历史消息 - 纯函数，不依赖 isStreaming
  const doLoadHistory = useCallback(
    async (sid: string | null) => {
      if (!sid) {
        setMessages([])
        return
      }

      try {
        const history = await getConversationHistory(sid)
        setMessages(history.messages)
        if (history.messages.length > 0) {
          const lastMsg = history.messages[history.messages.length - 1]
          if (lastMsg.metadata?.status === 'waiting_review') {
            setSessionStatus('waiting_review')
          } else {
            setSessionStatus('completed')
          }
        }
      } catch (error) {
        console.error('Failed to load history:', error)
        setMessages([])
      }
    },
    [setMessages, setSessionStatus]
  )

  // 监听 sessionId 变化加载历史
  // 注意：只在用户主动切换会话时加载，不在流结束时加载
  useEffect(() => {
    if (sessionId) {
      doLoadHistory(sessionId)
    }
  }, [sessionId])

  // 发送消息
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return

      // 标记为新会话，避免 status 事件触发时加载历史覆盖消息
      isNewSessionRef.current = !sessionId

      const newSessionId = sessionId || `sess_${Date.now()}`

      // 添加用户消息
      const userMsg = createUserMessage(content)
      addMessage(userMsg)

      // 添加空的助手消息 (流式填充)
      const assistantMsg = createAssistantMessage()
      addMessage(assistantMsg)

      setIsStreaming(true)
      setSessionStatus('active')

      const requestData: ChatRequest = {
        message: content,
        session_id: newSessionId,
        collection,
        stream: true,
      }

      try {
        eventSourceRef.current = createStreamRequest(
          requestData,
          (event) => {
            try {
              const data = JSON.parse(event.data)

              switch (data.event || event.type) {
                case 'token':
                  updateLastMessage((prev) => ({
                    ...prev,
                    content: prev.content + (data.content || data.data),
                  }))
                  break

                case 'citation':
                  updateLastMessage((prev) => ({
                    ...prev,
                    metadata: {
                      ...prev.metadata,
                      citations: data.citations || JSON.parse(data.data),
                    },
                  }))
                  break

                case 'status':
                  const statusData = typeof data === 'string' ? JSON.parse(data) : data
                  // 只有在不是新会话时才更新 activeSession（新会话的 sessionId 在 sendMessage 中已设置）
                  if (
                    !isNewSessionRef.current &&
                    statusData.session_id &&
                    statusData.session_id !== sessionId
                  ) {
                    setActiveSession(statusData.session_id)
                  }
                  // 重置新会话标志
                  isNewSessionRef.current = false
                  if (statusData.status === 'waiting_review') {
                    setSessionStatus('waiting_review')
                  }
                  break

                case 'done':
                  const doneData = typeof data === 'string' ? JSON.parse(data) : data
                  updateLastMessage((prev) => ({
                    ...prev,
                    metadata: {
                      ...prev.metadata,
                      confidence: doneData.confidence,
                      model_used: doneData.model_used,
                      fallback_used: doneData.fallback_used,
                      cache_hit: doneData.cache_hit,
                      latency_ms: doneData.latency_ms,
                      tokens_used: doneData.tokens_used,
                    },
                  }))
                  setSessionStatus('completed')
                  setIsStreaming(false)
                  break

                case 'error':
                  const errorData = typeof data === 'string' ? JSON.parse(data) : data
                  updateLastMessage((prev) => ({
                    ...prev,
                    content: `⚠️ 发生错误: ${errorData.error || errorData.data}`,
                  }))
                  setIsStreaming(false)
                  setSessionStatus('completed')
                  break

                default:
                  // 通用消息处理
                  if (data.content) {
                    updateLastMessage((prev) => ({
                      ...prev,
                      content: prev.content + data.content,
                    }))
                  }
              }
            } catch {
              // 解析失败，忽略
            }
          },
          (error) => {
            console.error('Stream error:', error)
            message.error('请求失败，请稍后重试')
            updateLastMessage((prev) => ({
              ...prev,
              content: '⚠️ 请求失败，请稍后重试。',
            }))
            setIsStreaming(false)
            setSessionStatus('completed')
          }
        )
      } catch (error) {
        console.error('Chat error:', error)
        updateLastMessage((prev) => ({
          ...prev,
          content: '⚠️ 请求失败，请稍后重试。',
        }))
        setIsStreaming(false)
        setSessionStatus('completed')
      }
    },
    [
      sessionId,
      collection,
      isStreaming,
      addMessage,
      updateLastMessage,
      setSessionStatus,
      setActiveSession,
    ]
  )

  // 停止生成
  const stopStreaming = useCallback(() => {
    eventSourceRef.current?.close()
    abortControllerRef.current?.abort()
    setIsStreaming(false)
    updateLastMessage((prev) => ({
      ...prev,
      content: prev.content + '\n\n[生成已停止]',
    }))
  }, [updateLastMessage])

  // 加载历史的包装函数（供外部调用）
  const loadHistory = useCallback(() => {
    return doLoadHistory(sessionId)
  }, [sessionId, doLoadHistory])

  return {
    messages,
    isStreaming,
    sessionStatus,
    sendMessage,
    stopStreaming,
    loadHistory,
  }
}
