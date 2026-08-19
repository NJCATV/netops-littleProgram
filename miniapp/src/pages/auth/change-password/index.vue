<template>
  <view class="page">
    <view class="panel form-card">
      <view class="page-title">修改密码</view>
      <view class="field">
        <view class="field-label">原密码</view>
        <input v-model="oldPassword" class="input" password placeholder="请输入原密码" placeholder-class="placeholder" />
      </view>
      <view class="field">
        <view class="field-label">新密码</view>
        <input v-model="newPassword" class="input" password placeholder="请输入新密码" placeholder-class="placeholder" />
      </view>
      <view class="field">
        <view class="field-label">确认新密码</view>
        <input v-model="confirmPassword" class="input" password placeholder="请再次输入新密码" placeholder-class="placeholder" />
      </view>
      <button class="primary-button submit-button" :loading="submitting" :disabled="submitting" @tap="submit">保存</button>
      <button class="skip-button" :disabled="submitting" @tap="skip">暂时跳过</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { changePassword, redirectByNextAction } from '../../../api/auth'
import { messageLabel } from '../../../utils/labels'

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const submitting = ref(false)

function skip() {
  uni.switchTab({ url: '/pages/workbench/index' })
}

function submit() {
  if (!oldPassword.value || !newPassword.value) {
    uni.showToast({ title: '请填写原密码和新密码', icon: 'none' })
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    uni.showToast({ title: '两次新密码不一致', icon: 'none' })
    return
  }

  submitting.value = true
  changePassword(oldPassword.value, newPassword.value)
    .then((data) => {
      uni.showToast({ title: '密码已修改', icon: 'success' })
      redirectByNextAction(data.next_action)
    })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => {
      submitting.value = false
    })
}
</script>

<style scoped>
.form-card {
  padding: 30rpx;
}

.page-title {
  margin-bottom: 28rpx;
  color: #1f2933;
  font-size: 34rpx;
  font-weight: 700;
}

.field + .field {
  margin-top: 22rpx;
}

.submit-button {
  width: 100%;
  margin-top: 34rpx;
}

.skip-button {
  width: 100%;
  margin-top: 18rpx;
  border: 0;
  background: transparent;
  color: #64748b;
  font-size: 28rpx;
}
</style>
