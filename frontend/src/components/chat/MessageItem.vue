<script setup lang="ts">
import { computed } from 'vue'
import { User, Service } from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types/chat'
import { renderMarkdown } from '@/utils/markdown'
import ReferenceCard from './ReferenceCard.vue'
import FeedbackBar from './FeedbackBar.vue'

const props = defineProps<{ message: ChatMessage }>()

const isUser = computed(() => props.message.role === 'user')
const html = computed(() => renderMarkdown(props.message.content))

// 答案状态标签
const stateTag = computed(() => {
  const m = props.message
  if (m.blocked) return { text: '已拦截', type: 'warning' as const }
  if (m.isNoAnswer) return { text: '未找到资料', type: 'info' as const }
  if (m.fromFaq) return { text: '标准答复', type: 'success' as const }
  return null
})

const refs = computed(() => props.message.references || [])
// 已完成的助手消息(有后端ID、非流式中)才显示赞踩
const showFeedback = computed(
  () => !isUser.value && !!props.message.id && !props.message.streaming,
)
</script>

<template>
  <div class="msg" :class="isUser ? 'msg-user' : 'msg-assistant'">
    <el-avatar :size="32" class="avatar">
      <el-icon><User v-if="isUser" /><Service v-else /></el-icon>
    </el-avatar>

    <div class="bubble-wrap">
      <div class="bubble" :class="{ 'is-no-answer': message.isNoAnswer, 'is-blocked': message.blocked }">
        <el-tag v-if="stateTag" :type="stateTag.type" size="small" class="state-tag">
          {{ stateTag.text }}
        </el-tag>
        <div v-if="isUser" class="user-text">{{ message.content }}</div>
        <template v-else>
          <div v-if="message.streaming && !message.content" class="thinking">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            <span class="thinking-text">正在思考…</span>
          </div>
          <div v-else class="md-body" v-html="html"></div>
          <span v-if="message.streaming && message.content" class="cursor">▍</span>
        </template>
      </div>

      <!-- 引用来源：可展开卡片 -->
      <ReferenceCard v-if="refs.length" :references="refs" />

      <!-- 赞踩 -->
      <FeedbackBar v-if="showFeedback" :message-id="message.id!" />
    </div>
  </div>
</template>

<style scoped>
.msg {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.msg-user {
  flex-direction: row-reverse;
}
.avatar {
  flex-shrink: 0;
  background: #e0e7ff;
  color: #1e40af;
}
.msg-user .avatar {
  background: #2563eb;
  color: #fff;
}
.bubble-wrap {
  max-width: 72%;
}
.bubble {
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  line-height: 1.7;
  word-break: break-word;
}
.msg-user .bubble {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
.bubble.is-no-answer {
  background: #f3f4f6;
  color: #6b7280;
}
.bubble.is-blocked {
  background: #fff7ed;
  border-color: #fdba74;
  color: #c2410c;
}
.state-tag {
  margin-bottom: 6px;
}
.user-text {
  white-space: pre-wrap;
}
.md-body :deep(p) {
  margin: 0 0 8px;
}
.md-body :deep(p:last-child) {
  margin-bottom: 0;
}
.md-body :deep(ul),
.md-body :deep(ol) {
  margin: 4px 0 8px;
  padding-left: 22px;
}
.md-body :deep(li) {
  margin: 2px 0;
}
.md-body :deep(code) {
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.9em;
}
.md-body :deep(pre) {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 12px;
  overflow-x: auto;
}
.md-body :deep(h1),
.md-body :deep(h2),
.md-body :deep(h3) {
  font-size: 1.05em;
  margin: 10px 0 6px;
}
.md-body :deep(strong) {
  font-weight: 600;
}
.thinking {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #9ca3af;
}
.thinking .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: bounce 1.2s infinite ease-in-out;
}
.thinking .dot:nth-child(2) {
  animation-delay: 0.2s;
}
.thinking .dot:nth-child(3) {
  animation-delay: 0.4s;
}
.thinking-text {
  margin-left: 4px;
  font-size: 13px;
}
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
.cursor {
  animation: blink 1s steps(1) infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
</style>
