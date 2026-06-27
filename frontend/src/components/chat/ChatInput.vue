<script setup lang="ts">
import { computed, ref } from 'vue'
import type { InputInstance } from 'element-plus'
import { Promotion, Close } from '@element-plus/icons-vue'

const props = defineProps<{ sending: boolean }>()
const emit = defineEmits<{ send: [text: string]; cancel: [] }>()

const text = ref('')
const inputRef = ref<InputInstance>()

const canSend = computed(() => text.value.trim().length > 0 && !props.sending)

function onSend() {
  if (!canSend.value) return
  emit('send', text.value.trim())
  text.value = ''
}

function onCancel() {
  emit('cancel')
}

// Enter 发送，Shift+Enter 换行
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (props.sending) {
      onCancel()
    } else {
      onSend()
    }
  }
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<template>
  <div class="chat-input">
    <el-input
      ref="inputRef"
      v-model="text"
      type="textarea"
      :rows="2"
      :autosize="{ minRows: 2, maxRows: 6 }"
      resize="none"
      :placeholder="sending ? '正在生成回答，Enter 终止，Shift+Enter 换行' : '请输入你的问题，Enter 发送，Shift+Enter 换行'"
      @keydown="onKeydown"
    />
    <el-button
      v-if="!sending"
      type="primary"
      :icon="Promotion"
      :disabled="!canSend"
      class="send-btn"
      @click="onSend"
    >
      发送
    </el-button>
    <el-button
      v-else
      type="danger"
      :icon="Close"
      class="send-btn cancel-btn"
      @click="onCancel"
    >
      终止
    </el-button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.75);
  border-top: 1px solid var(--glass-border-solid);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.send-btn {
  flex-shrink: 0;
  height: 40px;
  background: linear-gradient(135deg, #4facfe, #00d4ff);
  border: none;
  color: #0a0e27;
  font-weight: 600;
}
.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #00d4ff, #4facfe);
  color: #0a0e27;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cancel-btn {
  background: linear-gradient(135deg, #f87171, #ef4444);
  border: none;
  color: #ffffff;
  font-weight: 600;
}
.cancel-btn:hover {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #ffffff;
}
</style>
