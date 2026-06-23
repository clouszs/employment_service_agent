<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as userApi from '@/api/user'
import type { Role } from '@/types/user'

const loading = ref(false)
const rows = ref<Role[]>([])

async function load() {
  loading.value = true
  try {
    rows.value = await userApi.listRoles()
  } finally {
    loading.value = false
  }
}
onMounted(load)

const dialogVisible = ref(false)
const editing = ref<Role | null>(null)
const form = reactive({ role_code: '', role_name: '', description: '' })

function openCreate() {
  editing.value = null
  form.role_code = ''
  form.role_name = ''
  form.description = ''
  dialogVisible.value = true
}
function openEdit(row: Role) {
  editing.value = row
  form.role_code = row.role_code
  form.role_name = row.role_name
  form.description = row.description || ''
  dialogVisible.value = true
}
async function submit() {
  if (!form.role_name.trim()) return ElMessage.warning('请填写角色名称')
  if (editing.value) {
    await userApi.updateRole(editing.value.id, { role_name: form.role_name, description: form.description })
    ElMessage.success('已更新')
  } else {
    if (!form.role_code.trim()) return ElMessage.warning('请填写角色编码')
    await userApi.createRole({ ...form })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreate">新建角色</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="role_code" label="编码" width="160" />
      <el-table-column prop="role_name" label="名称" width="160" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色' : '新建角色'" width="420px">
      <el-form label-width="80px">
        <el-form-item label="编码" required>
          <el-input v-model="form.role_code" :disabled="!!editing" placeholder="如：editor" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.role_name" placeholder="如：知识库编辑" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}
</style>
