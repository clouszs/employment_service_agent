<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, Plus, Delete, SwitchButton } from '@element-plus/icons-vue'
import * as settingsApi from '@/api/app-configs'
import type { AppConfig } from '@/api/app-configs'

/** 系统设置：展示全部配置项，提供新建 / 删除 / 启用-禁用 */
const groups = [
  { key: 'all', label: '全部' },
  { key: 'qa_strategy', label: '问答策略' },
  { key: 'qa_retrieval', label: '检索参数' },
  { key: 'qa_model', label: '模型配置' },
  { key: 'qa_other', label: '其他' },
]

const activeGroup = ref('all')
const loading = ref(false)
const saving = ref(false)
const deletingId = ref<number | null>(null)
const seeding = ref(false)
const savingPreset = ref(false)
const presetValues = reactive<Record<string, string>>({})
const allConfigs = ref<AppConfig[]>([])
const loadError = ref('')
const originalSnapshot = reactive<Record<number, AppConfig>>({})
const editingRows = reactive<Record<number, boolean>>({})
const editCache = reactive<Record<number, AppConfig>>({})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const form = reactive<Partial<AppConfig>>({
  config_key: '',
  config_value: '',
  description: '',
  group_name: '',
  is_sensitive: 0,
  status: 1,
})
const editingRowId = ref<number | null>(null)

const filteredData = computed<AppConfig[]>(() => {
  const base = allConfigs.value
  if (activeGroup.value === 'all') return base
  return base.filter((item) => (item.group_name || 'qa_other') === activeGroup.value)
})

const dirtyCount = computed(() => {
  let n = 0
  for (const id of Object.keys(editingRows)) {
    if (editingRows[Number(id)]) n++
  }
  return n
})

function openCreateDialog() {
  dialogMode.value = 'create'
  editingRowId.value = null
  Object.assign(form, {
    config_key: '',
    config_value: '',
    description: '',
    group_name: activeGroup.value === 'all' ? '' : activeGroup.value,
    is_sensitive: 0,
    status: 1,
  })
  dialogVisible.value = true
}

function openEditDialog(row: AppConfig) {
  dialogMode.value = 'edit'
  editingRowId.value = row.id
  Object.assign(form, {
    config_key: row.config_key,
    config_value: row.config_value,
    description: row.description ?? '',
    group_name: row.group_name ?? '',
    is_sensitive: row.is_sensitive,
    status: row.status,
  })
  dialogVisible.value = true
}

async function submitDialog() {
  if (!form.config_key) {
    ElMessage.warning('请填写配置键')
    return
  }
  try {
    if (dialogMode.value === 'create') {
      await settingsApi.createConfig({
        config_key: form.config_key,
        config_value: form.config_value ?? '',
        description: form.description ?? null,
        group_name: form.group_name || 'qa_other',
        is_sensitive: form.is_sensitive ?? 0,
        status: form.status ?? 1,
      })
      ElMessage.success('配置已创建')
    } else if (editingRowId.value) {
      await settingsApi.updateAppConfig(editingRowId.value, {
        config_value: form.config_value ?? '',
        description: form.description ?? null,
        group_name: form.group_name || 'qa_other',
        is_sensitive: form.is_sensitive ?? 0,
        status: form.status ?? 1,
      })
      ElMessage.success('配置已更新')
    }
    dialogVisible.value = false
    await loadAll()
  } catch {
    ElMessage.error('操作失败，请重试')
  }
}

function startEdit(id: number): void {
  const row = allConfigs.value.find((r) => r.id === id)
  if (!row || row.is_sensitive === 1) return
  editingRows[id] = true
  editCache[id] = { ...row }
}

function commitEdit(id: number): void {
  const row = allConfigs.value.find((r) => r.id === id)
  const cached = editCache[id]
  if (!row || !cached) return
  row.config_value = cached.config_value
  row.description = cached.description
  editingRows[id] = false
  delete editCache[id]
}

async function saveAll(): Promise<void> {
  if (dirtyCount.value === 0) {
    ElMessage.info('没有需要保存的修改')
    return
  }
  saving.value = true
  try {
    const toSave: AppConfig[] = []
    for (const id of Object.keys(editingRows)) {
      if (editingRows[Number(id)]) {
        const cached = editCache[Number(id)]
        if (cached) toSave.push(cached)
      }
    }
    for (const item of toSave) {
      await settingsApi.updateAppConfig(item.id, {
        config_value: item.config_value,
        description: item.description,
      })
    }
    await loadAll()
    ElMessage.success(`已保存 ${toSave.length} 项配置`)
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function resetAll(): void {
  for (const id of Object.keys(editingRows)) {
    editingRows[Number(id)] = false
    delete editCache[Number(id)]
  }
  for (const [id, snap] of Object.entries(originalSnapshot)) {
    const row = allConfigs.value.find((r) => r.id === Number(id))
    if (row) {
      row.config_value = snap.config_value
      row.description = snap.description
    }
  }
  ElMessage.info('已放弃未保存的修改')
}

async function handleDelete(row: AppConfig) {
  try {
    await ElMessageBox.confirm(`确定删除配置「${row.config_key}」吗？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  deletingId.value = row.id
  try {
    await settingsApi.deleteConfig(row.id)
    ElMessage.success('配置已删除')
    await loadAll()
  } catch {
    ElMessage.error('删除失败，请重试')
  } finally {
    deletingId.value = null
  }
}

async function handleToggle(row: AppConfig) {
  try {
    const next = row.status === 1 ? 0 : 1
    await settingsApi.toggleAppConfigStatus(row.id, next)
    ElMessage.success(next === 1 ? '已启用' : '已禁用')
    await loadAll()
  } catch {
    ElMessage.error('操作失败，请重试')
  }
}

function maskedValue(v: string): string {
  if (!v) return '（空）'
  if (v.length <= 4) return '****'
  return '*'.repeat(Math.min(v.length, 12))
}

async function loadAll(): Promise<void> {
  loading.value = true
  try {
    const res = await settingsApi.listConfigs({ page: 1, size: 200 })
    allConfigs.value = res.items
    Object.assign(
      originalSnapshot,
      Object.fromEntries(res.items.map((item: AppConfig) => [item.id, { ...item }])),
    )
    const liveIds = new Set(res.items.map((i: AppConfig) => i.id))
    for (const id of Object.keys(editingRows)) {
      if (!liveIds.has(Number(id))) {
        editingRows[Number(id)] = false
        delete editCache[Number(id)]
      }
    }
  } catch {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const QA_PRESETS = [
  { label: '检索返回条数', key: 'qa_retrieval.top_k', value: '5', group: 'qa_retrieval' },
  { label: 'FAQ匹配条数', key: 'qa_retrieval.faq_top_k', value: '1', group: 'qa_retrieval' },
  { label: 'FAQ命中阈值', key: 'qa_retrieval.faq_score_threshold', value: '0.75', group: 'qa_retrieval' },
  { label: '检索无答案阈值', key: 'qa_retrieval.score_threshold', value: '0.4', group: 'qa_retrieval' },
  { label: 'LLM模型', key: 'qa_model.model', value: 'qwen3.7-max', group: 'qa_model' },
  { label: '回答创造性', key: 'qa_model.temperature', value: '0.3', group: 'qa_model' },
  { label: '最大生成长度', key: 'qa_model.max_tokens', value: '0', group: 'qa_model' },
  { label: '显示引用来源', key: 'qa_strategy.enable_reference', value: '1', group: 'qa_strategy' },
  { label: '启用无答案兜底', key: 'qa_strategy.no_answer_enabled', value: '1', group: 'qa_strategy' },
]

function applyPreset(preset: { key: string; value: string; group: string }) {
  form.config_key = preset.key
  form.config_value = preset.value
  form.group_name = preset.group
  form.description = preset.key
  form.status = 1
  form.is_sensitive = 0
}

async function handleSeedDefaults() {
  seeding.value = true
  try {
    await loadAll()
    let created = 0
    for (const item of QA_PRESETS) {
      const existing = allConfigs.value.find((c) => c.config_key === item.key)
      if (!existing) {
        await settingsApi.upsertConfig({
          config_key: item.key,
          config_value: item.value,
          description: item.label,
          group_name: item.group,
          is_sensitive: 0,
          status: 1,
        })
        created++
      }
    }
    ElMessage.success(`已初始化 ${created} 项默认配置`)
    await syncPresetValues()
  } catch {
    ElMessage.error('初始化默认配置失败')
  } finally {
    seeding.value = false
  }
}

async function syncPresetValues() {
  for (const item of QA_PRESETS) {
    const found = allConfigs.value.find((c) => c.config_key === item.key)
    presetValues[item.key] = found ? found.config_value : item.value
  }
}

async function handleSavePresets() {
  savingPreset.value = true
  try {
    for (const item of QA_PRESETS) {
      const val = presetValues[item.key] ?? item.value
      await settingsApi.upsertConfig({
        config_key: item.key,
        config_value: val,
        description: item.label,
        group_name: item.group,
        is_sensitive: 0,
        status: 1,
      })
    }
    ElMessage.success('问答参数已保存')
    await loadAll()
    await syncPresetValues()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingPreset.value = false
  }
}

function handleResetPresets() {
  for (const item of QA_PRESETS) {
    presetValues[item.key] = item.value
  }
}

onMounted(async () => {
  await loadAll()
  await syncPresetValues()
})
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
      <p class="subtitle">管理系统配置与问答策略参数</p>
    </div>

    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建配置</el-button>
      <el-button :loading="saving" @click="saveAll">
        {{ saving ? '保存中...' : '保存全部修改' }}
      </el-button>
      <el-button @click="resetAll">放弃修改</el-button>
      <span v-if="dirtyCount > 0" class="dirty-hint">有 {{ dirtyCount }} 项未保存</span>
      <el-button @click="loadAll" :loading="loading">刷新</el-button>
      <el-button type="success" :loading="seeding" @click="handleSeedDefaults">初始化默认配置</el-button>
    </div>

    <el-card class="qa-preset-card" shadow="never">
      <template #header>
        <div class="preset-header">
          <span class="preset-title">问答参数快速配置</span>
          <span class="preset-tip">修改后点保存，下一问答请求即时生效</span>
        </div>
      </template>
      <div class="preset-grid">
        <div v-for="item in QA_PRESETS" :key="item.key" class="preset-item">
          <label class="preset-label">{{ item.label }}</label>
          <el-input v-model="presetValues[item.key]" size="small" :placeholder="item.value" />
        </div>
      </div>
      <div class="preset-actions">
        <el-button type="primary" :loading="savingPreset" @click="handleSavePresets">保存参数</el-button>
        <el-button @click="handleResetPresets">恢复默认</el-button>
      </div>
    </el-card>

    <el-tabs v-model="activeGroup" class="group-tabs">
      <el-tab-pane v-for="g in groups" :key="g.key" :label="g.label" :name="g.key">
        <template #label><span class="tab-label">{{ g.label }}</span></template>

        <el-table :data="filteredData" :loading="loading" stripe style="width: 100%">
          <el-table-column label="配置键" min-width="220">
            <template #default="{ row }">
              <code class="key-cell">{{ row.config_key }}</code>
            </template>
          </el-table-column>

          <el-table-column label="当前值" min-width="320">
            <template #default="{ row }">
              <template v-if="row.is_sensitive === 1">
                <span class="masked-value">{{ maskedValue(row.config_value) }}</span>
                <el-tooltip content="敏感配置，不允许编辑" placement="top">
                  <el-icon class="lock-icon"><Lock /></el-icon>
                </el-tooltip>
              </template>
              <template v-else>
                <el-input
                  v-if="editingRows[row.id]"
                  v-model="editCache[row.id].config_value"
                  size="small"
                  placeholder="配置值"
                  @blur="commitEdit(row.id)"
                  @keyup.enter="commitEdit(row.id)"
                />
                <span v-else class="value-cell" @dblclick="startEdit(row.id)">
                  {{ row.config_value || '<span class="empty-hint">（空）</span>' }}
                </span>
              </template>
            </template>
          </el-table-column>

          <el-table-column label="说明" width="220">
            <template #default="{ row }">
              <el-input
                v-if="editingRows[row.id]"
                v-model="editCache[row.id].description"
                size="small"
                placeholder="配置说明"
                @blur="commitEdit(row.id)"
              />
              <span v-else class="desc-cell" @dblclick="startEdit(row.id)">
                {{ row.description || '-' }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="分组" width="120" align="center">
            <template #default="{ row }">{{ row.group_name || '-' }}</template>
          </el-table-column>

          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" effect="plain">
                {{ row.status === 1 ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.is_sensitive !== 1"
                text
                type="primary"
                size="small"
                @click="startEdit(row.id)"
              >
                编辑
              </el-button>
              <el-button
                text
                type="warning"
                size="small"
                :icon="SwitchButton"
                @click="handleToggle(row)"
              >
                {{ row.status === 1 ? '禁用' : '启用' }}
              </el-button>
              <el-button
                text
                type="danger"
                size="small"
                :icon="Delete"
                :loading="deletingId === row.id"
                @click="handleDelete(row)"
              />
            </template>
          </el-table-column>
        </el-table>

        <div v-if="filteredData.length === 0 && !loading" class="empty-group">
          该分组暂无配置项
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建配置' : '编辑配置'"
      width="520px"
      @closed="editingRowId = null"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="配置键" required>
          <el-input v-model="form.config_key" :disabled="dialogMode === 'edit'" placeholder="如 qa_strategy.max_tokens" />
        </el-form-item>
        <el-form-item label="当前值">
          <el-input v-model="form.config_value" placeholder="配置值" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" placeholder="可选说明" />
        </el-form-item>
        <el-form-item label="分组">
          <el-select v-model="form.group_name" placeholder="选择分组" style="width: 100%">
            <el-option label="问答策略" value="qa_strategy" />
            <el-option label="检索参数" value="qa_retrieval" />
            <el-option label="模型配置" value="qa_model" />
            <el-option label="其他" value="qa_other" />
          </el-select>
        </el-form-item>
        <el-form-item label="敏感">
          <el-switch v-model="form.is_sensitive" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitDialog">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 1100px;
}
.page-header {
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  color: #1f2937;
}
.subtitle {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.dirty-hint {
  font-size: 13px;
  color: #fbbf24;
}
.group-tabs {
  background: #ffffff;
  border: 1px solid #e5e7eb;
}
.tab-label {
  font-size: 14px;
}
.key-cell {
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #7dd3fc;
  background: rgba(125, 211, 252, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}
.value-cell {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px dashed transparent;
  transition: all 0.15s;
  min-height: 32px;
  display: inline-block;
  width: 100%;
}
.value-cell:hover {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}
.empty-hint {
  color: #6b7280;
  font-style: italic;
}
.masked-value {
  font-family: monospace;
  color: #6b7280;
  user-select: none;
}
.lock-icon {
  margin-left: 6px;
  color: #f59e0b;
  vertical-align: middle;
}
.desc-cell {
  cursor: pointer;
  color: #6b7280;
  font-size: 13px;
}
.empty-group {
  text-align: center;
  color: #6b7280;
  padding: 40px 0;
  font-size: 14px;
}
.qa-preset-card {
  margin-bottom: 16px;
}
.preset-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.preset-title {
  font-weight: 600;
  color: #334155;
}
.preset-tip {
  font-size: 12px;
  color: #6b7280;
}
.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.preset-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preset-label {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}
.preset-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
@media (max-width: 1200px) {
  .preset-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
