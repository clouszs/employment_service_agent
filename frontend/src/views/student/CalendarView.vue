<template>
  <div class="calendar-view">
    <div class="page-header">
      <h2>面试日程</h2>
      <p class="subtitle">创建面试日程并导出为日历文件</p>
    </div>

    <el-card class="form-card">
      <el-form :model="form" label-width="100px">
        <el-form-item label="事件标题" required>
          <el-input v-model="form.title" placeholder="如：腾讯一面" clearable />
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-input v-model="form.start_time" placeholder="如：2026-07-01T14:00:00" clearable />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-input v-model="form.end_time" placeholder="缺省为开始时间 +1 小时" clearable />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="如：北京 / 腾讯会议号" clearable />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="面试官、岗位、准备事项" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleGenerate">生成日程</el-button>
          <el-button :disabled="!icsResult" @click="handleDownload">下载 .ics</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="icsResult" class="preview-card">
      <template #header>
        <div class="preview-header">
          <span>预览：{{ icsResult.title }}</span>
          <span class="preview-time">{{ icsResult.start_time }} ~ {{ icsResult.end_time }}</span>
        </div>
      </template>
      <pre class="ics-preview">{{ icsResult.ics_content }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as careerApi from '@/api/career'

const loading = ref(false)
const icsResult = ref<{ ics_content: string; title: string; start_time: string; end_time: string } | null>(null)

const form = reactive({
  title: '',
  start_time: '',
  end_time: '',
  location: '',
  description: '',
})

async function handleGenerate() {
  if (!form.title || !form.start_time) {
    ElMessage.warning('请填写标题和开始时间')
    return
  }
  loading.value = true
  try {
    const res = await careerApi.buildCalendarIcs({
      title: form.title,
      start_time: form.start_time,
      end_time: form.end_time || undefined,
      location: form.location || undefined,
      description: form.description || undefined,
    })
    icsResult.value = res
    ElMessage.success('日程生成成功')
  } catch (err: any) {
    ElMessage.error(err.message || '生成失败')
  } finally {
    loading.value = false
  }
}

function handleDownload() {
  if (!icsResult.value) return
  const blob = new Blob([icsResult.value.ics_content], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${icsResult.value.title || 'interview'}.ics`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.calendar-view {
  max-width: 900px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 22px;
}
.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
}
.form-card {
  margin-bottom: 20px;
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.preview-time {
  color: #6b7280;
  font-size: 13px;
}
.ics-preview {
  background: #f9fafb;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
