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
    messages.value.push({ role: 'user', content: q })
    const assistant: ChatMessage = { role: 'assistant', content: '', streaming: true }
    messages.value.push(assistant)
    sending.value = true
    const isNew = currentId.value === null

    try {
      const result = (await chatApi.askAgent(q, currentId.value ?? undefined)) as AgentAskResult
      Object.assign(assistant, toAgentChatMessage(result))
      currentId.value = result.conversation_id || currentId.value
    } catch (e) {
      if (!assistant.content) {
        assistant.content = e instanceof Error ? e.message : '回答失败，请稍后重试。'
        assistant.isNoAnswer = true
        assistant.isError = true
      }
      assistant.streaming = false
    } finally {
      sending.value = false
      if (isNew && currentId.value !== null) {
        await loadConversations()
      }
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
  }
})
