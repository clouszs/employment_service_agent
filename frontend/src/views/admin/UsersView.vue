<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import * as userApi from '@/api/user'
import type { Role, User } from '@/types/user'

const USER_TYPE: Record<number, string> = {
  1: '学生',
  2: '毕业生',
  3: '辅导员',
  4: '老师',
  5: '管理员',
}

const loading = ref(false)
const rows = ref<User[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '' })
const allRoles = ref<Role[]>([])

async function load() {
  loading.value = true
  try {
    const res = await userApi.listUsers({ page: query.page, size: query.size, keyword: query.keyword || undefined })
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
  allRoles.value = await userApi.listRoles().catch(() => [])
  load()
})

// 新建/编辑
const dialogVisible = ref(false)
const editing = ref<User | null>(null)
const form = reactive({
  username: '',
  password: '',
  real_name: '',
  user_type: 1,
  college: '',
  status: 1,
})
function openCreate() {
  editing.value = null
  Object.assign(form, { username: '', password: '', real_name: '', user_type: 1, college: '', status: 1 })
  dialogVisible.value = true
}
function openEdit(row: User) {
  editing.value = row
  Object.assign(form, {
    username: row.username,
    password: '',
    real_name: row.real_name || '',
    user_type: row.user_type,
    college: row.college || '',
    status: row.status,
  })
  dialogVisible.value = true
}
async function submit() {
  if (editing.value) {
    await userApi.updateUser(editing.value.id, {
      real_name: form.real_name,
      user_type: form.user_type,
      college: form.college,
      status: form.status,
    })
    ElMessage.success('已更新')
  } else {
    if (!form.username.trim() || form.password.length < 6) return ElMessage.warning('账号必填，密码≥6位')
    await userApi.createUser({ ...form })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function disable(row: User) {
  try {
    await ElMessageBox.confirm(`禁用用户「${row.real_name || row.username}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await userApi.deleteUser(row.id)
  ElMessage.success('已禁用')
  load()
}

// 物理删除（仅非管理员账户）
async function hardDelete(row: User) {
  try {
    await ElMessageBox.confirm(
      `确定彻底删除用户「${row.real_name || row.username}」？此操作不可恢复！`,
      '危险操作',
      { type: 'error', confirmButtonText: '彻底删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await userApi.hardDeleteUser(row.id)
    ElMessage.success('已彻底删除')
    load()
  } catch {
    /* 拦截器已提示（如不可删管理员） */
  }
}

// 分配角色
const roleDialog = ref(false)
const roleTarget = ref<User | null>(null)
const selectedRoles = ref<number[]>([])
async function openRoles(row: User) {
  roleTarget.value = row
  const rs = await userApi.getUserRoles(row.id)
  selectedRoles.value = rs.map((r) => r.id)
  roleDialog.value = true
}
async function submitRoles() {
  if (!roleTarget.value) return
  await userApi.assignRoles(roleTarget.value.id, selectedRoles.value)
  ElMessage.success('角色已分配，类型已同步')
  roleDialog.value = false
  load() // 刷新列表，使联动后的“类型”同步显示
}

// 重置密码
const pwdDialog = ref(false)
const pwdTarget = ref<User | null>(null)
const newPwd = ref('')
function openResetPwd(row: User) {
  pwdTarget.value = row
  newPwd.value = ''
  pwdDialog.value = true
}
async function submitResetPwd() {
  if (!pwdTarget.value) return
  if (newPwd.value.length < 6) return ElMessage.warning('新密码至少 6 位')
  await userApi.resetPassword(pwdTarget.value.id, newPwd.value)
  ElMessage.success('密码已重置')
  pwdDialog.value = false
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="账号/姓名搜索"
        clearable
        style="width: 220px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-button type="primary" :icon="Refresh" @click="onSearch">查询</el-button>
      <div class="spacer" />
      <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="账号" width="140" />
      <el-table-column prop="real_name" label="姓名" width="120" />
      <el-table-column label="类型" width="100" align="center">
        <template #default="{ row }">{{ USER_TYPE[row.user_type] || row.user_type }}</template>
      </el-table-column>
      <el-table-column prop="college" label="学院" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" effect="plain">
            {{ row.status === 1 ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="360" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" size="small" @click="openRoles(row)">分配角色</el-button>
          <el-button link type="warning" size="small" @click="openResetPwd(row)">重置密码</el-button>
          <el-button link type="info" size="small" @click="disable(row)">禁用</el-button>
          <el-button
            v-if="row.user_type !== 5"
            link
            type="danger"
            size="small"
            @click="hardDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
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

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新建用户'" width="460px">
      <el-form label-width="80px">
        <el-form-item label="账号" required>
          <el-input v-model="form.username" :disabled="!!editing" placeholder="学工号/用户名" />
        </el-form-item>
        <el-form-item v-if="!editing" label="密码" required>
          <el-input v-model="form.password" type="password" show-password placeholder="≥6位" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.user_type" style="width: 100%">
            <el-option v-for="(t, k) in USER_TYPE" :key="k" :label="t" :value="Number(k)" />
          </el-select>
        </el-form-item>
        <el-form-item label="学院">
          <el-input v-model="form.college" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="pwdDialog" title="重置密码" width="380px">
      <div class="reset-tip">为用户「{{ pwdTarget?.real_name || pwdTarget?.username }}」设置新密码</div>
      <el-input
        v-model="newPwd"
        type="password"
        show-password
        placeholder="新密码（至少 6 位）"
        @keyup.enter="submitResetPwd"
      />
      <template #footer>
        <el-button @click="pwdDialog = false">取消</el-button>
        <el-button type="primary" @click="submitResetPwd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色 -->
    <el-dialog v-model="roleDialog" title="分配角色" width="360px">
      <el-checkbox-group v-model="selectedRoles">
        <el-checkbox v-for="r in allRoles" :key="r.id" :value="r.id" :label="r.id">
          {{ r.role_name }}（{{ r.role_code }}）
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRoles">保存</el-button>
      </template>
    </el-dialog>
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
.reset-tip {
  margin-bottom: 12px;
  color: #6b7280;
  font-size: 13px;
}
</style>
