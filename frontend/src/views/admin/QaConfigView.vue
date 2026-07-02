<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock, Plus, Delete, SwitchButton } from '@element-plus/icons-vue'
import * as settingsApi from '@/api/app-configs'
import type { AppConfig } from '@/api/app-configs'

/** 问答策略预设分组 */
const QA_GROUPS = [
  { key: 'qa_strategy', label: '问答策略' },
  { key: 'qa_retrieval', label: '检索参数' },
  { key: 'qa_model', label: '模型配置' },
  { key: 'qa_other', label: '其他' },
]

const activeGroup = ref(QA_GROUPS[0].key)
const loading = ref(false)
const saving = ref(false)
const deletingId = ref<number | null>(null)
const allConfigs = ref<AppConfig[]>([])
const originalSnapshot = reactive<Record<number, AppConfig>>({})
const editingRows = reactive<Record<number, boolean>>({})
const editCache = reactive<Record<number, AppConfig>>({})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingRowId = ref<number | null>(null)
const form = reactive<Partial<AppConfig>>({
  config_key: '',
  config_value: '',
  description: '',
  group_name: QA_GROUPS[0].key,
  is_sensitive: 0,
  status: 1,
})

/** 过滤出 qa_ 前缀配置 */
const qaConfigs = computed<AppConfig[]>(() =>
  allConfigs.value.filter((item) => item.config_key.startsWith('qa_')),
)

/** 按分组归类 */
const groupedData = computed<Record<string, AppConfig[]>>(() => {
  const map: Record<string, AppConfig[]> = {}
  for (const g of QA_GROUPS) map[g.key] = []
  for (const item of qaConfigs.value) {
    const group = item.group_name && map[item.group_name] !== undefined
      ? item.group_name
      : 'qa_other'
    map[group].push(item)
  }
  for (const k of Object.keys(map)) {
    map[k].sort((a, b) => a.config_key.localeCompare(b.config_key))
  }
  return map
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
    config_key: 'qa_',
    config_value: '',
    description: '',
    group_name: activeGroup.value,
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
    group_name: row.group_name ?? 'qa_other',
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
  if (!String(form.config_key).startsWith('qa_')) {
    ElMessage.warning('问答策略配置的 key 必须以 qa_ 开头')
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
    const res = await settingsApi.listConfigs({})
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

onMounted(loadAll)
</script>

<template>
  <div class="qa-config-page">
    <div class="page-header">
      <h2>智能问答配置</h2>
      <p class="subtitle">
        管理问答策略、检索参数和模型配置（仅展示 config_key 以 qa_ 开头的配置项）
      </p>
    </div>

    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建配置</el-button>
      <el-button :loading="saving" @click="saveAll">
        {{ saving ? '保存中...' : '保存全部修改' }}
      </el-button>
      <el-button @click="resetAll">放弃修改</el-button>
      <span v-if="dirtyCount > 0" class="dirty-hint">有 {{ dirtyCount }} 项未保存</span>
      <el-button @click="loadAll" :loading="loading">刷新</el-button>
    </div>

    <el-tabs v-model="activeGroup" type="border-card" class="group-tabs">
      <el-tab-pane
        v-for="group in QA_GROUPS"
        :key="group.key"
        :label="group.label"
        :name="group.key"
      >
        <template #label>
          <span class="tab-label">{{ group.label }}</span>
        </template>

        <el-table :data="groupedData[group.key]" :loading="loading" stripe style="width: 100%">
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

          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" effect="plain">
                {{ row.status === 1 ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="180" align="center" fixed="right">
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

        <div v-if="(groupedData[group.key]?.length ?? 0) === 0" class="empty-group">
          该分组暂无配置项
        </div>
      </el-tab-pane>
    </el-tabs>

    <div v-if="qaConfigs.length === 0 && !loading" class="empty-tip">
      <el-empty description="暂无 qa_ 前缀配置项">
        <template #extra>
          <el-text type="info" size="small">
            请在「系统设置」中新建 key 以 qa_ 开头的配置项
          </el-text>
        </template>
      </el-empty>
    </div>

    <!-- 新建 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建配置' : '编辑配置'"
      width="520px"
      @closed="editingRowId = null"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="配置键" required>
          <el-input v-model="form.config_key" placeholder="如 qa_strategy.max_tokens" />
        </el-form-item>
        <el-form-item label="当前值">
          <el-input v-model="form.config_value" placeholder="配置值" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" placeholder="可选说明" />
        </el-form-item>
        <el-form-item label="分组">
          <el-select v-model="form.group_name" placeholder="选择分组" style="width: 100%">
            <el-option v-for="g in QA_GROUPS" :key="g.key" :label="g.label" :value="g.key" />
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
.qa-config-page {
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
.empty-tip {
  margin-top: 20px;
}
</style>
