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
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :locale="zhCn"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择结束时间"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :locale="zhCn"
            style="width: 100%"
          />
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
import { zhCn } from 'element-plus/es/locale/index.mjs'
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
  if (form.end_time && form.end_time <= form.start_time) {
    ElMessage.warning('结束时间必须晚于开始时间')
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
  color: #1f2937;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}
.subtitle {
  margin: 0;
  font-size: 14px;
  color: #334155;
}
.form-card {
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.preview-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.preview-time {
  color: #475569;
  font-size: 14px;
  font-weight: 500;
}
.ics-preview {
  background: #f8fafc;
  padding: 18px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
  color: #1e293b;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
}
</style>
