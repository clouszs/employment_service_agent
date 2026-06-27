<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, Refresh } from '@element-plus/icons-vue'
import * as settingsApi from '@/api/app-configs'
import type { AppConfig } from '@/api/settings'

// ── 预设分组：仅展示 qa_ 前缀配置 ──────────────────────────
const GROUPS = [
  { key: 'qa_strategy', label: '问答策略' },
  { key: 'qa_retrieval', label: '检索参数' },
  { key: 'qa_model', label: '模型配置' },
  { key: 'qa_other', label: '其他' },
]

const activeGroup = ref(GROUPS[0].key)
const loading = ref(false)
const saving = ref(false)
const allConfigs = ref<AppConfig[]>([])
const originalSnapshot = reactive<Record<number, AppConfig>>({})

// 行内编辑状态
const editingRows = reactive<Record<number, boolean>>({})
const editCache = reactive<Record<number, AppConfig>>({})

// ── 计算属性：只保留 qa_ 前缀并按分组聚合 ──────────────────
const qaConfigs = computed<AppConfig[]>(() =>
  allConfigs.value.filter((item) => item.config_key.startsWith('qa_')),
)

const groupedData = computed<Record<string, AppConfig[]>>(() => {
  const map: Record<string, AppConfig[]> = {}
  for (const g of GROUPS) map[g.key] = []
  for (const item of qaConfigs.value) {
    const g = (item.group_name && map[item.group_name] !== undefined)
      ? item.group_name
      : 'qa_other'
    map[g].push(item)
  }
  for (const k of Object.keys(map)) {
    map[k].sort((a, b) => a.config_key.localeCompare(b.config_key))
  }
  return map
})

const dirtyCount = computed(() => {
  let n = 0
  for (const id of Object.keys(editingRows) as number[]) {
    if (editingRows[id]) n++
  }
  return n
})

// ── 行内编辑逻辑 ──────────────────────────────────────────────
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

// ── 保存 / 重置 ───────────────────────────────────────────────
async function saveAll(): Promise<void> {
  if (dirtyCount.value === 0) {
    ElMessage.info('没有需要保存的修改')
    return
  }
  saving.value = true
  try {
    const toSave: AppConfig[] = []
    for (const id of Object.keys(editingRows) as number[]) {
      if (editingRows[id]) {
        const cached = editCache[id]
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
  for (const id of Object.keys(editingRows) as number[]) {
    editingRows[id] = false
    delete editCache[id]
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

// ── 工具函数 ─────────────────────────────────────────────────
function maskedValue(v: string): string {
  if (!v) return '（空）'
  if (v.length <= 4) return '****'
  return '*'.repeat(Math.min(v.length, 12))
}

// ── 数据加载 ─────────────────────────────────────────────────
async function loadAll(): Promise<void> {
  loading.value = true
  try {
    const res = await settingsApi.listAppConfigs({})
    allConfigs.value = res.items
    Object.assign(
      originalSnapshot,
      Object.fromEntries(
        res.items.map((item: AppConfig) => [item.id, { ...item }]),
      ),
    )
    const liveIds = new Set(res.items.map((i: AppConfig) => i.id))
    for (const id of Object.keys(editingRows) as number[]) {
      if (!liveIds.has(Number(id))) {
        editingRows[id] = false
        delete editCache[id]
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
      <p class="subtitle">管理问答策略、检索参数和模型配置（仅展示 config_key 以 qa_ 开头的配置项）</p>
    </div>

    <!-- 统一操作栏 -->
    <div class="toolbar">
      <el-button type="primary" :loading="saving" @click="saveAll">
        {{ saving ? '保存中...' : '保存全部修改' }}
      </el-button>
      <el-button @click="resetAll">放弃修改</el-button>
      <span v-if="dirtyCount > 0" class="dirty-hint">
        有 {{ dirtyCount }} 项未保存
      </span>
      <el-button :icon="Refresh" @click="loadAll" :loading="loading">刷新</el-button>
    </div>

    <!-- 分组 Tab -->
    <el-tabs v-model="activeGroup" type="border-card" class="group-tabs">
      <el-tab-pane
        v-for="group in GROUPS"
        :key="group.key"
        :label="group.label"
        :name="group.key"
      >
        <template #label>
          <span class="tab-label">{{ group.label }}</span>
        </template>

        <el-table
          :data="groupedData[group.key]"
          :loading="loading"
          stripe
          style="width: 100%"
        >
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

          <el-table-column label="说明" width="200">
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

          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                {{ row.status === 1 ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="(groupedData[group.key]?.length ?? 0) === 0" class="empty-group">
          该分组暂无配置项
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 提示：尚无 qa_ 配置时引导至系统设置 -->
    <el-empty
      v-if="qaConfigs.length === 0 && !loading"
      description="暂无 qa_ 前缀配置项"
      class="empty-tip"
    >
      <template #extra>
        <el-text type="info" size="small">
          请在「系统设置」中新建 group_name 为问答策略/检索参数/模型配置 的 qa_ 配置项
        </el-text>
      </template>
    </el-empty>
  </div>
</template>

<style scoped>
.qa-config-page {
  max-width: 960px;
}
.page-header {
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  color: #e2e8f0;
}
.subtitle {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
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
  background: #0f1a2e;
  border: 1px solid #1e2d4a;
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
  color: #64748b;
  font-style: italic;
}
.masked-value {
  font-family: monospace;
  color: #94a3b8;
  user-select: none;
}
.lock-icon {
  margin-left: 6px;
  color: #f59e0b;
  vertical-align: middle;
}
.desc-cell {
  cursor: pointer;
  color: #cbd5e1;
  font-size: 13px;
}
.empty-group {
  text-align: center;
  color: #64748b;
  padding: 40px 0;
  font-size: 14px;
}
.empty-tip {
  margin-top: 20px;
}
</style>
