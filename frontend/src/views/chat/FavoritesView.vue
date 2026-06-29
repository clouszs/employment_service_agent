<template>
  <div class="favorites-page">
    <div class="page-header">
      <h2>我的收藏</h2>
      <p class="subtitle">收藏过的问答消息，支持添加备注</p>
    </div>

    <el-table
      :data="rows"
      :loading="loading"
      stripe
      style="width: 100%"
      @row-click="onRowClick"
    >
      <el-table-column label="消息摘要" min-width="360" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="snippet-cell">
            <el-icon class="snippet-icon"><ChatDotSquare /></el-icon>
            <span>{{ row.message_snippet || '正在加载...' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="备注" width="180">
        <template #default="{ row }">
          <span v-if="row.note" class="note-preview">{{ row.note }}</span>
          <span v-else class="note-empty">无备注</span>
        </template>
      </el-table-column>
      <el-table-column label="收藏时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="!row.note"
            size="small"
            text
            type="primary"
            @click.stop="openNoteDialog(row)"
          >
            加备注
          </el-button>
          <el-button
            v-else
            size="small"
            text
            type="info"
            @click.stop="openNoteDialog(row)"
          >
            编辑备注
          </el-button>
          <el-button size="small" text type="danger" @click.stop="onRemove(row)"> 删除 </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="load"
        @size-change="load"
      />
    </div>

    <!-- 备注弹窗 -->
    <el-dialog v-model="noteDialogVisible" title="备注" width="420px" @closed="resetNoteForm">
      <el-input v-model="noteForm.note" type="textarea" :rows="3" placeholder="添加备注（可选）" />
      <template #footer>
        <el-button @click="noteDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="noteSubmitting" @click="submitNote">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotSquare } from '@element-plus/icons-vue'
import * as favApi from '@/api/favorites'
import type { FavoriteItem } from '@/types/favorites'

const router = useRouter()

const loading = ref(false)
const rows = ref<FavoriteItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10 })

async function load() {
  loading.value = true
  try {
    const res = await favApi.listFavorites({ page: query.page, size: query.size })
    rows.value = res.items
    total.value = res.total
    // 反查每条收藏的消息摘要和会话 ID
    await enrichSnippets(rows.value)
  } finally {
    loading.value = false
  }
}

async function enrichSnippets(items: FavoriteItem[]) {
  await Promise.all(
    items.map(async (item) => {
      try {
        const res = await favApi.getMessageDetail(item.message_id)
        const msg = res.data
        item.message_snippet = (msg.content || '').slice(0, 120)
        item.conversation_id = msg.conversation_id ?? null
      } catch {
        item.message_snippet = '（消息已删除）'
      }
    }),
  )
}

function onRowClick(row: FavoriteItem) {
  if (row.conversation_id) {
    router.push({ path: '/student/chat', query: { conversation_id: String(row.conversation_id) } })
  }
}

// 备注弹窗
const noteDialogVisible = ref(false)
const editingFav = ref<FavoriteItem | null>(null)
const noteForm = reactive({ note: '' as string | null })
const noteSubmitting = ref(false)

function openNoteDialog(row: FavoriteItem) {
  editingFav.value = row
  noteForm.note = row.note ?? ''
  noteDialogVisible.value = true
}
function resetNoteForm() {
  editingFav.value = null
  noteForm.note = ''
}

async function submitNote() {
  if (!editingFav.value) return
  noteSubmitting.value = true
  try {
    const res = await favApi.updateFavorite(editingFav.value.id, { note: noteForm.note || null })
    const target = rows.value.find((r) => r.id === res.id)
    if (target) target.note = res.note
    ElMessage.success('备注已更新')
    noteDialogVisible.value = false
  } catch {
    ElMessage.error('更新失败')
  } finally {
    noteSubmitting.value = false
  }
}

async function onRemove(row: FavoriteItem) {
  try {
    await ElMessageBox.confirm('取消收藏该条消息？', '提示', { type: 'warning' })
    await favApi.deleteFavorite(row.id)
    rows.value = rows.value.filter((r) => r.id !== row.id)
    total.value = Math.max(0, total.value - 1)
    ElMessage.success('已取消收藏')
  } catch {
    /* cancelled */
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

onMounted(load)
</script>

<style scoped>
.favorites-page {
  max-width: 960px;
}
.page-header {
  margin-bottom: 20px;
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
.snippet-cell {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.6;
}
.snippet-icon {
  margin-top: 3px;
  color: #7dd3fc;
  flex-shrink: 0;
}
.note-preview {
  color: #fbbf24;
  font-size: 13px;
}
.note-empty {
  color: #64748b;
  font-size: 13px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
