import request from './request'
import API_ENDPOINTS from '@/config/api'
import type { ChatRequest, ChatResponse, SessionInfo, ConversationHistory } from '@/types/chat'

// SSE 流式请求
export function createStreamRequest(
  data: ChatRequest,
  onMessage: (event: MessageEvent) => void,
  onError?: (error: Error) => void
): EventSource {
  // 构建 SSE URL
  const url = new URL(API_ENDPOINTS.chatStream, window.location.origin)

  // 使用 fetch + ReadableStream 实现 POST 请求的 SSE
  const token = useAuthStore.getState().token

  const controller = new AbortController()

  fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify(data),
    signal: controller.signal,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No reader available')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let currentEventType = 'message'

      const read = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            // SSE 完成
            const event = new MessageEvent('done', { data: '' })
            onMessage(event)
            return
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            // 处理 event: 行（设置事件类型）
            if (line.startsWith('event: ')) {
              currentEventType = line.slice(7).trim()
              continue
            }

            // 处理 data: 行
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                const event = new MessageEvent('done', { data: '' })
                onMessage(event)
                return
              }

              try {
                const parsed = JSON.parse(data)
                const eventType = currentEventType || 'message'

                // token 事件的数据可能是字符串，需要包装成对象
                let finalData = parsed
                if (eventType === 'token' && typeof parsed === 'string') {
                  finalData = { content: parsed }
                }

                const event = new MessageEvent(eventType, {
                  data: JSON.stringify(finalData),
                })
                onMessage(event)

                // 重置事件类型
                currentEventType = 'message'
              } catch {
                // 可能是纯文本
                const event = new MessageEvent('message', {
                  data: JSON.stringify({ content: data }),
                })
                onMessage(event)
              }
            }
          }

          read()
        })
      }

      read()
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        onError?.(error)
      }
    })

  // 返回一个模拟的 EventSource 对象，用于外部控制
  return {
    close: () => controller.abort(),
  } as EventSource
}

// 获取会话列表
export async function getSessions(page = 1, pageSize = 20): Promise<SessionInfo[]> {
  const res = await request.get(API_ENDPOINTS.chatSessions, {
    params: { page, page_size: pageSize },
  })
  return res.data
}

// 获取对话历史
export async function getConversationHistory(
  sessionId: string,
  limit = 50
): Promise<ConversationHistory> {
  const res = await request.get(API_ENDPOINTS.chatHistory(sessionId), {
    params: { limit },
  })
  return res.data
}

// 删除会话
export async function deleteSession(sessionId: string): Promise<void> {
  await request.delete(API_ENDPOINTS.chatDeleteSession(sessionId))
}

// 导入 useAuthStore 用于 createStreamRequest
import { useAuthStore } from '@/stores/authStore'
