<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import { changePassword } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const visible = defineModel<boolean>({ default: false })

const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const USER_TYPE: Record<number, string> = {
  1: '学生',
  2: '毕业生',
  3: '辅导员',
  4: '老师',
  5: '管理员',
}

const pwd = reactive({ old_password: '', new_password: '', confirm: '' })
const submitting = ref(false)

// 打开时清空密码表单
watch(visible, (v) => {
  if (v) {
    pwd.old_password = ''
    pwd.new_password = ''
    pwd.confirm = ''
  }
})

async function submit() {
  if (!pwd.old_password) return ElMessage.warning('请输入旧密码')
  if (pwd.new_password.length < 6) return ElMessage.warning('新密码至少 6 位')
  if (pwd.new_password !== pwd.confirm) return ElMessage.warning('两次输入的新密码不一致')
  submitting.value = true
  try {
    await changePassword(pwd.old_password, pwd.new_password)
    ElMessage.success('密码修改成功')
    visible.value = false
  } catch {
    /* 拦截器已提示（如旧密码错） */
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="个人资料" width="440px">
    <!-- 基本信息（只读） -->
    <el-descriptions :column="1" border class="info">
      <el-descriptions-item label="账号">{{ user?.username }}</el-descriptions-item>
      <el-descriptions-item label="姓名">{{ user?.real_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="身份">{{ USER_TYPE[user?.user_type || 0] || '-' }}</el-descriptions-item>
      <el-descriptions-item label="学院">{{ user?.college || '-' }}</el-descriptions-item>
      <el-descriptions-item label="角色">{{ (user?.roles || []).join('、') || '-' }}</el-descriptions-item>
    </el-descriptions>

    <!-- 修改密码 -->
    <div class="pwd-title">修改密码</div>
    <el-form label-width="80px">
      <el-form-item label="旧密码">
        <el-input v-model="pwd.old_password" type="password" show-password placeholder="当前密码" />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="pwd.new_password" type="password" show-password placeholder="至少 6 位" />
      </el-form-item>
      <el-form-item label="确认">
        <el-input
          v-model="pwd.confirm"
          type="password"
          show-password
          placeholder="再次输入新密码"
          @keyup.enter="submit"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">修改密码</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.info {
  margin-bottom: 18px;
}
.pwd-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #374151;
}
</style>
