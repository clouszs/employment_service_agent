<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { ChatMessage } from '@/types/chat'
import MessageItem from './MessageItem.vue'

const props = defineProps<{ messages: ChatMessage[] }>()

const scrollRef = ref<HTMLElement>()

async function scrollToBottom() {
  await nextTick()
  const el = scrollRef.value
  if (el) el.scrollTop = el.scrollHeight
}

// 消息变化（新增或流式增量）时自动滚到底部
watch(
  () => [props.messages.length, props.messages[props.messages.length - 1]?.content],
  () => scrollToBottom(),
  { flush: 'post' },
)
</script>

<template>
  <div ref="scrollRef" class="msg-list">
    <MessageItem v-for="(m, i) in messages" :key="m.id ?? `tmp-${i}`" :message="m" />
  </div>
</template>

<style scoped>
.msg-list {
  height: 100%;
  overflow-y: auto;
  padding: 20px 16px;
}
</style>
