<template>
  <div class="resume-view">
    <div class="page-header">
      <h2>简历助手</h2>
      <p class="subtitle">基于你的档案生成专业简历</p>
    </div>

    <el-card class="form-card">
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

    <el-dialog v-model="resumeVisible" title="简历预览" width="720px" @closed="resetResume">
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
          <div v-for="(edu, idx) in resume.education" :key="idx" class="resume-item">
            <strong>{{ edu.school }}</strong> - {{ edu.major }} | {{ edu.degree }} | {{ edu.period }}
          </div>
        </div>

        <div v-if="resume.experience?.length" class="resume-section">
          <h4>工作经历</h4>
          <div v-for="(exp, idx) in resume.experience" :key="idx" class="resume-item">
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
          <div v-for="(proj, idx) in resume.projects" :key="idx" class="resume-item">
            <strong>{{ proj.name }}</strong>
            <p>{{ proj.desc }}</p>
            <ul v-if="proj.highlights?.length">
              <li v-for="(h, i) in proj.highlights" :key="i">{{ h }}</li>
            </ul>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">暂无简历数据</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as careerApi from '@/api/career'

const loading = ref(false)
const resumeVisible = ref(false)
const resume = ref<any>(null)

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
    if (!resume.value) {
      ElMessage.warning('简历生成异常，请重试')
      return
    }
    resumeVisible.value = true
    ElMessage.success('简历生成成功')
  } catch (err: any) {
    ElMessage.error(err.message || '生成失败')
  } finally {
    loading.value = false
  }
}

function resetResume() {
  resume.value = null
}
</script>

<style scoped>
.resume-view {
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
.resume-preview {
  padding: 8px 4px;
}
.resume-basics {
  margin-bottom: 20px;
}
.resume-basics h3 {
  margin: 0 0 6px;
  font-size: 20px;
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
}
.resume-item ul {
  margin: 6px 0 0 18px;
  padding: 0;
}
.skill-tag {
  margin: 0 6px 6px 0;
}
.empty-state {
  text-align: center;
  color: #6b7280;
  padding: 30px 0;
}
</style>
