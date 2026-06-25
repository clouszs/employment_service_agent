<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const emit = defineEmits<{
  send: [text: string]
}>()

const query = ref('')
const loading = ref(false)
const mode = ref<'agent' | 'search'>('agent')

async function onSubmit() {
  const q = query.value.trim()
  if (!q || loading.value) return
  loading.value = true
  try {
    emit('send', q)
  } finally {
    loading.value = false
    query.value = ''
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSubmit()
  }
}
</script>

<template>
  <div class="search-box">
    <div class="mode-switch">
      <el-button
        :type="mode === 'agent' ? 'primary' : 'default'"
        size="small"
        @click="mode = 'agent'"
      >
        AI 问答
      </el-button>
      <el-button
        :type="mode === 'search' ? 'primary' : 'default'"
        size="small"
        @click="mode = 'search'"
      >
        纯检索
      </el-button>
    </div>

    <div class="input-wrap">
      <el-input
        v-model="query"
        :disabled="loading"
        :placeholder="mode === 'agent' ? '请输入您的问题，AI 将为您解答...' : '仅检索知识库片段，不生成回答'"
        @keydown="onKeydown"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button
            :loading="loading"
            type="primary"
            @click="onSubmit"
          >
            提问
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<style scoped>
.search-box {
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
}
.mode-switch {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 10px;
}
.input-wrap :deep(.el-input) {
  --el-input-bg: rgba(15, 23, 42, 0.55);
  --el-input-border-color: rgba(56, 189, 248, 0.35);
  --el-input-text-color: #e0f2fe;
  --el-input-placeholder-color: #7dd3fc;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 12px;
  backdrop-filter: blur(20px);
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.15);
}
.input-wrap :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none !important;
  padding: 4px 12px;
}
.input-wrap :deep(.el-input__inner) {
  color: #e0f2fe;
  caret-color: #38bdf8;
}
.input-wrap :deep(.el-input__inner::placeholder) {
  color: #7dd3fc;
}
.input-wrap :deep(.el-input-group__append) {
  background: rgba(56, 189, 248, 0.15);
  border: none;
  border-radius: 0 12px 12px 0;
}
</style>
