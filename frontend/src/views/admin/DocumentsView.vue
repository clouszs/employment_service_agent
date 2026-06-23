<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadRawFile } from 'element-plus'
import { Plus, Refresh, UploadFilled } from '@element-plus/icons-vue'
import * as kbApi from '@/api/knowledge'
import type { Category, Chunk, KbDocument } from '@/types/knowledge'

// ---- 列表 ----
const loading = ref(false)
const rows = ref<KbDocument[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '', status: undefined as number | undefined })
const categories = ref<Category[]>([])

const PARSE_MAP: Record<number, { text: string; type: '' | 'info' | 'warning' | 'success' | 'danger' }> = {
  0: { text: '待解析', type: 'info' },
  1: { text: '解析中', type: 'warning' },
  2: { text: '成功', type: 'success' },
  3: { text: '失败', type: 'danger' },
}
const INDEX_MAP: Record<number, { text: string; type: '' | 'info' | 'warning' | 'success' | 'danger' }> = {
  0: { text: '未索引', type: 'info' },
  1: { text: '索引中', type: 'warning' },
  2: { text: '已索引', type: 'success' },
  3: { text: '失败', type: 'danger' },
}

async function load() {
  loading.value = true
  try {
    const res = await kbApi.listDocuments({
      page: query.page,
      size: query.size,
      keyword: query.keyword || undefined,
      status: query.status,
    })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  query.page = 1
  load()
}

onMounted(async () => {
  categories.value = await kbApi.listCategories().catch(() => [])
  load()
})

// ---- 上传 ----
const uploadVisible = ref(false)
const uploading = ref(false)
const uploadForm = reactive({
  title: '',
  category_id: undefined as number | undefined,
  source: '',
  confidential_level: 1,
  remark: '',
})
const selectedFile = ref<UploadRawFile | null>(null)

function openUpload() {
  uploadForm.title = ''
  uploadForm.category_id = undefined
  uploadForm.source = ''
  uploadForm.confidential_level = 1
  uploadForm.remark = ''
  selectedFile.value = null
  uploadVisible.value = true
}

function onFileChange(file: { raw?: UploadRawFile }) {
  selectedFile.value = file.raw || null
  if (selectedFile.value && !uploadForm.title) {
    uploadForm.title = selectedFile.value.name.replace(/\.[^.]+$/, '')
  }
}

async function submitUpload() {
  if (!selectedFile.value) return ElMessage.warning('请选择文件')
  if (!uploadForm.title.trim()) return ElMessage.warning('请填写标题')
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  fd.append('title', uploadForm.title)
  if (uploadForm.category_id) fd.append('category_id', String(uploadForm.category_id))
  if (uploadForm.source) fd.append('source', uploadForm.source)
  fd.append('confidential_level', String(uploadForm.confidential_level))
  if (uploadForm.remark) fd.append('remark', uploadForm.remark)
  uploading.value = true
  try {
    await kbApi.uploadDocument(fd)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    load()
  } catch (e) {
    ElMessage.error((e as Error).message || '上传失败')
  } finally {
    uploading.value = false
  }
}

// ---- 解析 / 入库 ----
async function doParse(row: KbDocument) {
  await kbApi.parseDocument(row.id)
  ElMessage.success('解析任务已提交')
  pollStatus(row.id, 'parse_status')
}

async function doIndex(row: KbDocument) {
  if (row.parse_status !== 2) return ElMessage.warning('请先解析成功再入库')
  await kbApi.indexDocument(row.id)
  ElMessage.success('入库任务已提交')
  pollStatus(row.id, 'index_status')
}

// 轮询单条文档状态直到完成
function pollStatus(id: number, field: 'parse_status' | 'index_status') {
  let n = 0
  const timer = setInterval(async () => {
    n++
    const doc = await kbApi.getDocument(id).catch(() => null)
    if (doc) {
      const idx = rows.value.findIndex((r) => r.id === id)
      if (idx >= 0) rows.value[idx] = doc
      if ([2, 3].includes(doc[field]) || n > 60) clearInterval(timer)
    } else if (n > 60) {
      clearInterval(timer)
    }
  }, 1500)
}

// ---- 删除 ----
async function doDelete(row: KbDocument) {
  try {
    await ElMessageBox.confirm(`确定删除文档《${row.title}》？将连带删除其分片与向量。`, '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await kbApi.deleteDocument(row.id)
  ElMessage.success('已删除')
  load()
}

// ---- 上下架 ----
async function toggleStatus(row: KbDocument) {
  const next = row.status === 1 ? 0 : 1
  await kbApi.updateDocument(row.id, { status: next })
  row.status = next
  ElMessage.success(next === 1 ? '已上架' : '已下架')
}

// ---- 分片查看 ----
const chunkVisible = ref(false)
const chunkLoading = ref(false)
const chunks = ref<Chunk[]>([])
const chunkDocTitle = ref('')

async function viewChunks(row: KbDocument) {
  chunkDocTitle.value = row.title
  chunkVisible.value = true
  chunkLoading.value = true
  try {
    chunks.value = await kbApi.listChunks(row.id)
  } finally {
    chunkLoading.value = false
  }
}
</script>

<template>
  <div class="doc-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="按标题搜索"
        clearable
        style="width: 240px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-select v-model="query.status" placeholder="上架状态" clearable style="width: 130px" @change="onSearch">
        <el-option label="已上架" :value="1" />
        <el-option label="已下架" :value="0" />
      </el-select>
      <el-button type="primary" :icon="Refresh" @click="onSearch">查询</el-button>
      <div class="spacer" />
      <el-button type="primary" :icon="Plus" @click="openUpload">上传文档</el-button>
    </div>

    <!-- 列表 -->
    <el-table v-loading="loading" :data="rows" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="file_type" label="类型" width="80" align="center" />
      <el-table-column label="解析" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="PARSE_MAP[row.parse_status].type" size="small">
            {{ PARSE_MAP[row.parse_status].text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="索引" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="INDEX_MAP[row.index_status].type" size="small">
            {{ INDEX_MAP[row.index_status].text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" effect="plain">
            {{ row.status === 1 ? '上架' : '下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="doParse(row)">解析</el-button>
          <el-button link type="primary" size="small" @click="doIndex(row)">入库</el-button>
          <el-button link type="primary" size="small" @click="viewChunks(row)">分片</el-button>
          <el-button link type="warning" size="small" @click="toggleStatus(row)">
            {{ row.status === 1 ? '下架' : '上架' }}
          </el-button>
          <el-button link type="danger" size="small" @click="doDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pager">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="load"
        @size-change="onSearch"
      />
    </div>

    <!-- 上传弹窗 -->
    <el-dialog v-model="uploadVisible" title="上传文档" width="520px">
      <el-form label-width="80px">
        <el-form-item label="文件" required>
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            accept=".txt,.md,.pdf"
            style="width: 100%"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此或<em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 txt / md / pdf，单个不超过 50MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="文档标题" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="uploadForm.category_id" placeholder="可选" clearable style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="uploadForm.source" placeholder="如：校就业指导中心" />
        </el-form-item>
        <el-form-item label="密级">
          <el-select v-model="uploadForm.confidential_level" style="width: 100%">
            <el-option label="公开" :value="1" />
            <el-option label="校内" :value="2" />
            <el-option label="受限" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="uploadForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 分片查看抽屉 -->
    <el-drawer v-model="chunkVisible" :title="`分片 - ${chunkDocTitle}`" size="46%">
      <div v-loading="chunkLoading">
        <el-empty v-if="!chunkLoading && chunks.length === 0" description="暂无分片，请先解析" />
        <div v-for="c in chunks" :key="c.id" class="chunk-item">
          <div class="chunk-head">
            <span>#{{ c.chunk_index }}</span>
            <span v-if="c.page_no">第{{ c.page_no }}页</span>
            <el-tag v-if="c.vector_id" size="small" type="success" effect="plain">已向量化</el-tag>
            <el-tag v-else size="small" type="info" effect="plain">未入库</el-tag>
          </div>
          <div class="chunk-content">{{ c.content }}</div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.spacer {
  flex: 1;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.chunk-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: #fafafa;
}
.chunk-head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.chunk-content {
  font-size: 13px;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
}
</style>
