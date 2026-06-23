<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'
import { submitFeedback } from '@/api/conversation'

const props = defineProps<{ messageId: number }>()

const current = ref<number | null>(null) // 1赞 -1踩 null未评价
const loading = ref(false)

// 点赞：弹窗输入原因（选填，可不填直接提交）
async function like() {
  if (loading.value) return
  let reason = ''
  try {
    const { value } = await ElMessageBox.prompt('可补充评价（选填）', '点赞反馈', {
      confirmButtonText: '提交',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '说说哪里有帮助（可留空）',
    })
    reason = (value || '').trim()
  } catch {
    return
  }
  await send(1, reason)
}

// 点踩：弹窗输入原因（必填，非空校验）
async function dislike() {
  if (loading.value) return
  let reason = ''
  try {
    const { value } = await ElMessageBox.prompt('请填写不满意的原因（必填）', '点踩反馈', {
      confirmButtonText: '提交',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '例如：答案不准确 / 不完整 / 答非所问',
      inputValidator: (v: string) => (v && v.trim() ? true : '输入不可为空'),
    })
    reason = (value || '').trim()
  } catch {
    return
  }
  await send(-1, reason)
}

async function send(rating: number, reason: string) {
  loading.value = true
  try {
    await submitFeedback(props.messageId, rating, reason || undefined)
    current.value = rating
    ElMessage.success('感谢反馈')
  } catch {
    // 错误（如敏感词拦截、点踩为空）由 axios 拦截器提示
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="feedback-bar">
    <el-button
      text
      size="small"
      :type="current === 1 ? 'primary' : 'default'"
      :icon="CaretTop"
      :disabled="loading"
      @click="like"
    >
      有用
    </el-button>
    <el-button
      text
      size="small"
      :type="current === -1 ? 'danger' : 'default'"
      :icon="CaretBottom"
      :disabled="loading"
      @click="dislike"
    >
      没用
    </el-button>
  </div>
</template>

<style scoped>
.feedback-bar {
  margin-top: 6px;
  display: flex;
  gap: 4px;
}
</style>
