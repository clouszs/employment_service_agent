import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as convApi from '@/api/conversation'
import { streamAsk } from '@/composables/useStreamChat'
import type { ChatMessage, Conversation, Message } from '@/types/chat'

function toChatMessage(m: Message): ChatMessage {
  return {
    id: m.id,
    role: m.role === 1 ? 'user' : 'assistant',
    content: m.content,
    isNoAnswer: m.is_no_answer === 1,
    fromFaq: m.answer_type === 2,
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

  // 进入新会话状态（暂不落库，首次提问时由后端自动建会话）
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

  // 流式问答（F5）：发问 → SSE 逐字追加 → done 补全引用与状态
  async function send(question: string) {
    const q = question.trim()
    if (!q || sending.value) return
    messages.value.push({ role: 'user', content: q })
    const assistant: ChatMessage = { role: 'assistant', content: '', streaming: true }
    messages.value.push(assistant)
    sending.value = true
    const isNew = currentId.value === null

    await streamAsk(q, currentId.value, {
      onDelta: (text) => {
        assistant.content += text
      },
      onDone: (meta) => {
        assistant.id = meta.message_id
        assistant.isNoAnswer = meta.is_no_answer
        assistant.blocked = meta.blocked
        assistant.fromFaq = meta.from_faq
        assistant.references = meta.references
        assistant.streaming = false
        currentId.value = meta.conversation_id
      },
      onError: (err) => {
        if (!assistant.content) {
          assistant.content = err.message || '回答失败，请稍后重试。'
          assistant.isNoAnswer = true
        }
        assistant.streaming = false
      },
    })

    sending.value = false
    if (isNew && currentId.value !== null) {
      await loadConversations()
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
    send,
  }
})
