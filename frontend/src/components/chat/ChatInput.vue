<script setup lang="ts">
import { computed, ref } from 'vue'
import type { InputInstance } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps<{ sending: boolean }>()
const emit = defineEmits<{ send: [text: string] }>()

const text = ref('')
const inputRef = ref<InputInstance>()

const canSend = computed(() => text.value.trim().length > 0 && !props.sending)

function onSend() {
  if (!canSend.value) return
  emit('send', text.value.trim())
  text.value = ''
}

// Enter 发送，Shift+Enter 换行
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
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
      placeholder="请输入你的问题，Enter 发送，Shift+Enter 换行"
      @keydown="onKeydown"
    />
    <el-button
      type="primary"
      :icon="Promotion"
      :loading="sending"
      :disabled="!canSend"
      class="send-btn"
      @click="onSend"
    >
      发送
    </el-button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e5e7eb;
}
.send-btn {
  flex-shrink: 0;
  height: 40px;
}
</style>
