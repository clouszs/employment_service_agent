import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as convApi from '@/api/conversation'
import * as chatApi from '@/api/chat'
import type { AgentAskResult, ChatMessage, Conversation, Message } from '@/types/chat'

function toChatMessage(m: Message): ChatMessage {
  return {
    id: m.id,
    role: m.role === 1 ? 'user' : 'assistant',
    content: m.content,
    isNoAnswer: m.is_no_answer === 1,
    fromFaq: m.answer_type === 2,
  }
}

function toAgentChatMessage(result: AgentAskResult): ChatMessage {
  return {
    id: result.message_id || undefined,
    role: 'assistant',
    content: result.response,
    isNoAnswer: result.is_no_answer,
    references: result.references,
    citations: result.citations,
    confidence: result.confidence,
    route: result.route,
    queryRiskLevel: result.query_risk_level,
    isLowConfidence: result.is_low_confidence,
    isError: result.is_error,
    consistencyIssues: result.consistency_issues,
    factIssues: result.fact_issues,
    temporalWarnings: result.temporal_warnings,
    warnings: result.warnings,
    requestId: result.request_id,
    llmTokensIn: result.llm_tokens_in,
    llmTokensOut: result.llm_tokens_out,
  }
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentId = ref<number | null>(null)
  const messages = ref<ChatMessage[]>([])
  const loadingList = ref(false)
  const loadingMessages = ref(false)
  const sending = ref(false)
  const _abortController = ref<AbortController | null>(null)

  async function loadConversations() {
    loadingList.value = true
    try {
      const res = await convApi.listConversations()
      conversations.value = res.items
    } finally {
      loadingList.value = false
    }
  }

  async function selectConversation(id: number) {
    currentId.value = id
    loadingMessages.value = true
    try {
      const detail = await convApi.getConversation(id)
      messages.value = (detail.messages || []).map(toChatMessage)
    } finally {
      loadingMessages.value = false
    }
  }

  function startNewConversation() {
    currentId.value = null
    messages.value = []
  }

  async function removeConversation(id: number) {
    await convApi.deleteConversation(id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (currentId.value === id) {
      startNewConversation()
    }
  }

  async function sendAgent(question: string) {
    const q = question.trim()
    if (!q || sending.value) return

    const controller = new AbortController()
    _abortController.value = controller

    messages.value.push({ role: 'user', content: q })
    const placeholder: ChatMessage = { role: 'assistant', content: '', streaming: true }
    messages.value.push(placeholder)
    const placeholderIndex = messages.value.length - 1
    sending.value = true
    const isNew = currentId.value === null

    try {
      const recentHistory = messages.value
        .filter((m) => m.role !== 'assistant' || (m.id && !m.streaming))
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }))
      const result = (await chatApi.askAgent(q, currentId.value ?? undefined, recentHistory, controller.signal)) as AgentAskResult
      const updated = toAgentChatMessage(result)
      messages.value[placeholderIndex] = updated
      currentId.value = result.conversation_id || currentId.value
    } catch (e) {
      if ((e as Error)?.name === 'AbortError' || (e as Error)?.message === 'aborted') {
        messages.value[placeholderIndex] = {
          ...placeholder,
          content: '已终止生成。',
          isNoAnswer: false,
          isError: false,
          streaming: false,
        }
        return
      }
      const fallback: ChatMessage = {
        ...placeholder,
        content: e instanceof Error ? e.message : '回答失败，请稍后重试。',
        isNoAnswer: true,
        isError: true,
        streaming: false,
      }
      messages.value[placeholderIndex] = fallback
    } finally {
      sending.value = false
      _abortController.value = null
      if (isNew && currentId.value !== null) {
        await loadConversations()
      }
    }
  }

  function cancelSend() {
    if (_abortController.value) {
      _abortController.value.abort()
    }
  }

  return {
    conversations,
    currentId,
    messages,
    loadingList,
    loadingMessages,
    sending,
    loadConversations,
    selectConversation,
    startNewConversation,
    removeConversation,
    sendAgent,
    cancelSend,
  }
})
