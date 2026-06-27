<script setup lang="ts">
import { computed } from 'vue'
import { User, Service, Warning } from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types/chat'
import { renderMarkdown } from '@/utils/markdown'
import ReferenceCard from './ReferenceCard.vue'
import FeedbackBar from './FeedbackBar.vue'
import ConfidenceBadge from './ConfidenceBadge.vue'
import TemporalWarning from './TemporalWarning.vue'
import RefusalMessage from './RefusalMessage.vue'

const props = defineProps<{ message: ChatMessage }>()

const isUser = computed(() => props.message.role === 'user')
const html = computed(() => renderMarkdown(props.message.content))

// 答案状态标签
const stateTag = computed(() => {
  const m = props.message
  if (m.isError) return { text: '系统错误', type: 'danger' as const }
  if (m.blocked) return { text: '已拦截', type: 'warning' as const }
  if (m.isNoAnswer) return { text: '未找到资料', type: 'info' as const }
  if (m.fromFaq) return { text: '标准答复', type: 'success' as const }
  return null
})

const refs = computed(() => props.message.references || props.message.citations || [])
// 已完成的助手消息(有后端ID、非流式中)才显示赞踩
const showFeedback = computed(
  () => !isUser.value && !!props.message.id && !props.message.streaming,
)
const showTemporal = computed(
  () => !isUser.value && !props.message.isNoAnswer && (props.message.temporalWarnings?.length ?? 0) > 0,
)
const factIssues = computed(() => props.message.factIssues || [])
const showFactIssues = computed(
  () => !isUser.value && factIssues.value.length > 0,
)
const unsupportedFactIssues = computed(
  () => factIssues.value.filter((issue) => (issue.unsupported_values || []).length > 0),
)
const showRefusal = computed(
  () => !isUser.value && !!props.message.isNoAnswer && !props.message.isError,
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

      <!-- 置信度 / 路由 / 时效 / 事实问题 / 拒答 -->
      <div v-if="!isUser" class="assistant-meta">
        <ConfidenceBadge v-if="message.confidence != null" :confidence="message.confidence" />
        <el-tag v-if="message.route" size="small" effect="plain" type="info">{{ message.route }}</el-tag>
        <el-tag v-if="message.queryRiskLevel" size="small" effect="plain" type="warning">
          {{ message.queryRiskLevel }}
        </el-tag>
        <el-tag v-if="message.isLowConfidence" size="small" effect="plain" type="danger">低置信度</el-tag>
        <TemporalWarning v-if="showTemporal" :warnings="message.temporalWarnings || []" />
        <div v-if="showFactIssues" class="fact-issues">
          <div class="fact-issues-head">
            <el-icon><Warning /></el-icon>
            <span>事实核验提示</span>
          </div>
          <ul class="fact-issues-list">
            <li v-for="(issue, i) in unsupportedFactIssues" :key="i">
              <span class="fact-label">{{ issue.label || issue.fact_type || '事实' }}未找到依据：</span>
              <span class="fact-value">{{ (issue.unsupported_values || []).join('、') }}</span>
            </li>
          </ul>
        </div>
        <RefusalMessage
          v-if="showRefusal"
          :is-no-answer="!!message.isNoAnswer"
          :reason="message.isNoAnswer ? '未在知识库找到匹配答案' : undefined"
          :route="message.route"
        />
      </div>

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
  background: rgba(79, 172, 254, 0.18);
  color: var(--accent-cyan);
}
.msg-user .avatar {
  background: linear-gradient(135deg, #4facfe, #00d4ff);
  color: #0a0e27;
}
.bubble-wrap {
  max-width: 72%;
}
.bubble {
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border-solid);
  color: var(--text-primary);
  line-height: 1.75;
  word-break: break-word;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.msg-user .bubble {
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.32), rgba(0, 212, 255, 0.32));
  color: #ffffff;
  border-color: rgba(79, 172, 254, 0.5);
}
.bubble.is-no-answer {
  background: rgba(148, 163, 184, 0.18);
  color: #e0e6f0;
  border-color: rgba(148, 163, 184, 0.35);
}
.bubble.is-blocked {
  background: rgba(251, 146, 60, 0.18);
  border-color: rgba(251, 146, 60, 0.45);
  color: #ffedd5;
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
  background: rgba(15, 23, 42, 0.6);
  color: var(--accent-cyan);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.9em;
  border: 1px solid rgba(79, 172, 254, 0.25);
}
.md-body :deep(pre) {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid var(--glass-border-solid);
  border-radius: 8px;
  padding: 10px 12px;
  overflow-x: auto;
  color: var(--text-secondary);
}
.md-body :deep(h1),
.md-body :deep(h2),
.md-body :deep(h3) {
  font-size: 1.05em;
  margin: 10px 0 6px;
  color: var(--accent-cyan);
}
.md-body :deep(strong) {
  font-weight: 600;
  color: #ffffff;
}
.md-body :deep(a) {
  color: var(--accent-blue);
}
.md-body :deep(blockquote) {
  border-left: 3px solid var(--accent-blue);
  padding-left: 10px;
  color: var(--text-muted);
  margin: 8px 0;
}
.md-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}
.md-body :deep(th),
.md-body :deep(td) {
  border: 1px solid rgba(79, 172, 254, 0.3);
  padding: 6px 10px;
  color: var(--text-secondary);
}
.md-body :deep(th) {
  background: rgba(79, 172, 254, 0.12);
  color: var(--accent-cyan);
  font-weight: 600;
}
.assistant-meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.fact-issues {
  width: 100%;
  margin-top: 4px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(251, 146, 60, 0.12);
  border: 1px solid rgba(251, 146, 60, 0.45);
}
.fact-issues-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-cyan);
  margin-bottom: 6px;
}
.fact-issues-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--text-secondary);
}
.fact-issues-list li + li {
  margin-top: 2px;
}
.fact-label {
  color: #fbbf24;
}
.fact-value {
  color: #ffffff;
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
