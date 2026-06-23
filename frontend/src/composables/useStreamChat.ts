import { getToken } from '@/api/request'
import type { Reference } from '@/types/chat'

export interface StreamDone {
  conversation_id: number
  message_id: number
  is_no_answer: boolean
  blocked?: boolean
  from_faq?: boolean
  references: Reference[]
}

export interface StreamError {
  code: number
  message: string
}

export interface StreamCallbacks {
  onDelta: (text: string) => void
  onDone: (meta: StreamDone) => void
  onError?: (err: StreamError) => void
  onHeartbeat?: () => void  // 心跳事件回调
}

/**
 * 流式问答：用 fetch + ReadableStream 读取后端 SSE。
 * 之所以不用 EventSource：它只支持 GET 且无法自定义请求头携带 JWT。
 *
 * 后端 SSE 格式：
 *   event: delta\n data: <文本片段>\n\n
 *   event: done\n data: <JSON>\n\n
 *   event: heartbeat\n data: <timestamp>\n\n  (可选的心跳保活)
 *   event: error\n data: <JSON>\n\n
 * (可选的错误事件)
 */
export async function streamAsk(
  question: string,
  conversationId: number | null,
  cb: StreamCallbacks,
): Promise<void> {
  const base = import.meta.env.VITE_API_BASE
  const token = getToken()

  // 超时检测
  const TIMEOUT_MS = 60000 // 60秒无响应视为超时
  let lastHeartbeat = Date.now()

  const checkTimeout = () => {
    if (Date.now() - lastHeartbeat > TIMEOUT_MS) {
      throw new Error('请求超时，请稍后重试')
    }
  }

  try {
    const resp = await fetch(`${base}/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        question,
        conversation_id: conversationId ?? undefined,
      }),
    })

    if (!resp.ok || !resp.body) {
      throw new Error(`流式请求失败: HTTP ${resp.status}`)
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    // 逐块读取，按 SSE 事件(空行分隔)解析
    for (;;) {
      checkTimeout() // 检查是否超时

      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let sep: number
      while ((sep = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, sep)
        buffer = buffer.slice(sep + 2)
        handleEvent(rawEvent, cb, () => {
          lastHeartbeat = Date.now() // 更新心跳时间
        })
      }
    }
    // 处理可能残留的最后一个事件
    if (buffer.trim()) handleEvent(buffer, cb, () => { lastHeartbeat = Date.now() })
  } catch (err) {
    cb.onError?.({ code: -1, message: err instanceof Error ? err.message : '网络错误' })
  }
}

function handleEvent(rawEvent: string, cb: StreamCallbacks, onHeartbeat: () => void): void {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of rawEvent.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      // 仅去掉 "data:" 后的单个前导空格，保留文本本身的空格
      dataLines.push(line.slice(5).replace(/^ /, ''))
    }
  }
  const data = dataLines.join('\n')

  if (event === 'delta') {
    // 后端把文字片段 JSON 编码后发送（带引号、转义换行），此处需解码还原真实文本
    try {
      cb.onDelta(JSON.parse(data))
    } catch {
      cb.onDelta(data)
    }
  } else if (event === 'done') {
    try {
      cb.onDone(JSON.parse(data) as StreamDone)
    } catch {
      /* 忽略解析失败 */
    }
  } else if (event === 'heartbeat') {
    // 心跳事件，更新超时计时器
    onHeartbeat()
    cb.onHeartbeat?.()
  } else if (event === 'error') {
    // 错误事件
    try {
      cb.onError?.(JSON.parse(data) as StreamError)
    } catch {
      cb.onError?.({ code: -1, message: data || '未知错误' })
    }
  }
}
