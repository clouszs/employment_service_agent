<template>
  <div class="resume-view">
    <div class="page-header">
      <h2>简历助手</h2>
      <p class="subtitle">基于你的档案生成专业简历，支持保存和多版本管理</p>
    </div>

    <div class="resume-layout">
      <!-- 左侧：生成表单 -->
      <div class="form-panel">
        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <span>生成新简历</span>
            </div>
          </template>
          <el-form :model="form" label-width="100px">
            <el-form-item label="目标岗位">
              <el-input v-model="form.target_job" placeholder="如：前端工程师、产品经理" clearable />
            </el-form-item>
            <el-form-item label="专业">
              <el-input v-model="form.extra_profile.major" placeholder="如：计算机科学与技术" clearable />
            </el-form-item>
            <el-form-item label="技能">
              <el-input v-model="form.extra_profile.skills" placeholder="如：Vue、Python、SQL（逗号分隔）" clearable />
            </el-form-item>
            <el-form-item label="经历">
              <el-input v-model="form.extra_profile.experience" type="textarea" :rows="3" placeholder="简要描述实习/项目经历" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleGenerate">生成简历</el-button>
              <el-button v-if="resume" @click="resumeVisible = false">关闭预览</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 我的简历列表 -->
        <el-card class="list-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>我的简历</span>
              <el-button type="primary" size="small" :icon="Refresh" @click="loadList" :loading="listLoading">刷新</el-button>
            </div>
          </template>

          <el-empty v-if="!listLoading && !resumes.length" description="暂无保存的简历" :image-size="60" />

          <div v-else class="resume-list">
            <div v-for="item in resumes" :key="item.id" class="resume-list-item" :class="{ default: item.is_default }">
              <div class="item-main" @click="openPreview(item)">
                <div class="item-title">
                  {{ item.title }}
                  <el-tag v-if="item.is_default" type="success" effect="plain" size="small">默认</el-tag>
                </div>
                <div class="item-meta">
                  {{ formatDate(item.updated_at) }}
                </div>
              </div>
              <div class="item-actions">
                <el-button size="small" text type="primary" @click="handleDownload(item)">下载 PDF</el-button>
                <el-button size="small" text type="default" @click="handleSetDefault(item)" :disabled="item.is_default">设为默认</el-button>
                <el-button size="small" text type="danger" @click="handleDelete(item)">删除</el-button>
              </div>
            </div>

            <div v-if="total > page * size" class="list-more">
              <el-button text type="primary" @click="loadMore">加载更多</el-button>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：简历预览 -->
      <div class="preview-panel">
        <el-card class="preview-card" shadow="never">
          <template #header>
            <div class="preview-header">
              <span class="preview-title">简历预览</span>
              <div v-if="resume" class="preview-actions">
                <el-button size="small" type="primary" @click="openSaveDialog">保存简历</el-button>
                <el-button size="small" @click="handleDownloadPdf">下载 PDF</el-button>
              </div>
            </div>
          </template>

          <div v-if="resume" class="resume-preview">
            <div class="resume-basics">
              <h3>{{ resume.basics?.name || '姓名' }}</h3>
              <p>{{ resume.basics?.title || '' }}</p>
              <p class="resume-contact">
                <span v-if="resume.basics?.email">{{ resume.basics.email }}</span>
                <span v-if="resume.basics?.phone"> | {{ resume.basics.phone }}</span>
                <span v-if="resume.basics?.location"> | {{ resume.basics.location }}</span>
              </p>
            </div>

            <div v-if="resume.summary" class="resume-section">
              <h4>个人简介</h4>
              <p>{{ resume.summary }}</p>
            </div>

            <div v-if="resume.education?.length" class="resume-section">
              <h4>教育经历</h4>
              <div v-for="(edu, idx) in resume.education" :key="'edu-'+idx" class="resume-item">
                <strong>{{ edu.school }}</strong> - {{ edu.major }} | {{ edu.degree }} | {{ edu.period }}
              </div>
            </div>

            <div v-if="resume.experience?.length" class="resume-section">
              <h4>工作经历</h4>
              <div v-for="(exp, idx) in resume.experience" :key="'exp-'+idx" class="resume-item">
                <strong>{{ exp.org }}</strong> - {{ exp.role }} | {{ exp.period }}
                <ul v-if="exp.highlights?.length">
                  <li v-for="(h, i) in exp.highlights" :key="i">{{ h }}</li>
                </ul>
              </div>
            </div>

            <div v-if="resume.skills?.length" class="resume-section">
              <h4>技能</h4>
              <el-tag v-for="(skill, idx) in resume.skills" :key="idx" class="skill-tag" type="success">{{ skill }}</el-tag>
            </div>

            <div v-if="resume.projects?.length" class="resume-section">
              <h4>项目经历</h4>
              <div v-for="(proj, idx) in resume.projects" :key="'proj-'+idx" class="resume-item">
                <strong>{{ proj.name }}</strong>
                <p>{{ proj.desc }}</p>
                <ul v-if="proj.highlights?.length">
                  <li v-for="(h, i) in proj.highlights" :key="i">{{ h }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-else class="empty-preview">
            <el-empty description="生成简历后在此预览" :image-size="80" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 保存弹窗 -->
    <el-dialog v-model="saveDialogVisible" title="保存简历" width="420px" @closed="resetSaveForm">
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="saveForm.title" placeholder="如：AI算法工程师简历" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="saveForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saveLoading" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as careerApi from '@/api/career'

const loading = ref(false)
const listLoading = ref(false)
const saveLoading = ref(false)
const resume = ref<any>(null)
const resumes = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const currentResumeId = ref<number | null>(null)

const saveDialogVisible = ref(false)
const saveForm = reactive({ title: '', is_default: false })

const form = reactive({
  target_job: '',
  extra_profile: {
    major: '',
    skills: '',
    experience: '',
  },
})

async function handleGenerate() {
  if (!form.target_job) {
    ElMessage.warning('请输入目标岗位')
    return
  }
  loading.value = true
  try {
    const extra: Record<string, any> = {}
    if (form.extra_profile.major) extra.major = form.extra_profile.major
    if (form.extra_profile.skills) extra.skills = form.extra_profile.skills.split(',').map((s) => s.trim()).filter(Boolean)
    if (form.extra_profile.experience) extra.experience = form.extra_profile.experience

    const res = await careerApi.generateResume({
      target_job: form.target_job,
      extra_profile: Object.keys(extra).length ? extra : undefined,
    })
    resume.value = res.resume || null
    currentResumeId.value = null
    if (!resume.value) {
      ElMessage.warning('简历生成异常，请重试')
      return
    }
    ElMessage.success('简历生成成功，请预览后保存')
  } catch (err: any) {
    ElMessage.error(err.message || '生成失败')
  } finally {
    loading.value = false
  }
}

function openPreview(item: any) {
  currentResumeId.value = item.id
  try {
    resume.value = typeof item.content === 'string' ? JSON.parse(item.content) : item.content
  } catch {
    resume.value = null
  }
}

function openSaveDialog() {
  if (!resume.value) {
    ElMessage.warning('请先生成简历')
    return
  }
  saveForm.title = form.target_job || '我的简历'
  saveForm.is_default = resumes.value.length === 0
  saveDialogVisible.value = true
}

function resetSaveForm() {
  saveForm.title = ''
  saveForm.is_default = false
}

async function handleSave() {
  if (!saveForm.title.trim()) {
    ElMessage.warning('请输入简历标题')
    return
  }
  saveLoading.value = true
  try {
    const res = await careerApi.saveResume({
      title: saveForm.title.trim(),
      content: resume.value,
      is_default: saveForm.is_default,
    })
    ElMessage.success('保存成功')
    saveDialogVisible.value = false
    currentResumeId.value = res.data.id
    await loadList()
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saveLoading.value = false
  }
}

async function loadList() {
  listLoading.value = true
  try {
    const res = await careerApi.listResumes({ page: page.value, size: size.value })
    resumes.value = res.items
    total.value = res.total
  } catch (err: any) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    listLoading.value = false
  }
}

function loadMore() {
  page.value += 1
  loadList()
}

async function handleDelete(item: any) {
  try {
    await ElMessageBox.confirm('确定删除该简历？', '提示', { type: 'warning' })
    await careerApi.deleteResume(item.id)
    resumes.value = resumes.value.filter((r) => r.id !== item.id)
    total.value = Math.max(0, total.value - 1)
    if (currentResumeId.value === item.id) {
      currentResumeId.value = null
      resume.value = null
    }
    ElMessage.success('已删除')
  } catch {
    /* cancelled */
  }
}

async function handleSetDefault(item: any) {
  try {
    await careerApi.setDefaultResume(item.id)
    resumes.value.forEach((r) => (r.is_default = r.id === item.id ? 1 : 0))
    ElMessage.success('已设为默认')
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}

async function handleDownload(item: any) {
  try {
    const blob = await careerApi.downloadResumePdf(item.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${item.title || '简历'}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  }
}

async function handleDownloadPdf() {
  if (currentResumeId.value) {
    await handleDownload({ id: currentResumeId.value, title: form.target_job || '简历' })
    return
  }
  if (!resume.value) {
    ElMessage.warning('请先生成简历')
    return
  }
  // 先保存再下载
  try {
    const res = await careerApi.saveResume({
      title: saveForm.title || form.target_job || '我的简历',
      content: resume.value,
      is_default: false,
    })
    currentResumeId.value = res.data.id
    await handleDownload({ id: res.data.id, title: res.data.title })
    await loadList()
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  }
}

function formatDate(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.resume-view {
  max-width: 1200px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  color: #1e293b;
}
.subtitle {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}
.resume-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}
.form-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.list-card {
  flex: 1;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.resume-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.resume-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
  cursor: pointer;
}
.resume-list-item:hover {
  border-color: #93c5fd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.resume-list-item.default {
  border-color: #10b981;
  background: #f0fdf4;
}
.item-main {
  flex: 1;
  min-width: 0;
}
.item-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.item-meta {
  font-size: 12px;
  color: #9ca3af;
}
.item-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.list-more {
  text-align: center;
  padding: 8px;
}
.preview-panel {
  position: sticky;
  top: 0;
}
.preview-card {
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.preview-title {
  font-weight: 600;
  color: #1f2937;
}
.resume-preview {
  padding: 4px;
}
.resume-basics {
  margin-bottom: 20px;
}
.resume-basics h3 {
  margin: 0 0 6px;
  font-size: 20px;
  color: #111827;
}
.resume-contact {
  color: #6b7280;
  font-size: 13px;
  margin: 4px 0 0;
}
.resume-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}
.resume-section h4 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #111827;
}
.resume-item {
  margin-bottom: 10px;
  line-height: 1.6;
  color: #4b5563;
}
.resume-item ul {
  margin: 6px 0 0 18px;
  padding: 0;
}
.skill-tag {
  margin: 0 6px 6px 0;
}
.empty-preview {
  text-align: center;
  padding: 60px 0;
}
</style>
