<template>
  <view class="page login-page">
    <view class="brand">
      <view class="brand-title">智维助手</view>
      <view class="brand-subtitle">江苏有线南京分公司</view>
    </view>

    <view class="panel login-panel">
      <view class="field">
        <view class="field-label">用户名 / 手机号 / OSS 账号</view>
        <input
          v-model.trim="account"
          class="input"
          placeholder="请输入登录账号"
          placeholder-class="placeholder"
          confirm-type="next"
        />
      </view>

      <view class="field">
        <view class="field-label">密码</view>
        <view class="password-row">
          <input
            v-model="password"
            class="password-input"
            placeholder="请输入密码"
            placeholder-class="placeholder"
            :password="!passwordVisible"
            confirm-type="done"
            @confirm="submit"
          />
          <button class="password-toggle" @tap="passwordVisible = !passwordVisible">
            {{ passwordVisible ? '隐藏' : '显示' }}
          </button>
        </view>
      </view>

      <view class="login-options">
        <text v-if="savedAccountFilled">已填入上次登录账号</text>
        <text v-else></text>
        <text v-if="checkingSession">正在检查登录状态...</text>
      </view>
      <view class="security-note">为保护公网账号安全，小程序不保存明文密码；有效登录令牌会自动恢复会话。</view>

      <button class="primary-button login-button" :loading="submitting" :disabled="!canSubmit || submitting" @tap="submit">
        登录
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  getLastLoginAccount,
  getMe,
  hasToken,
  login,
  redirectByNextAction
} from '../../api/auth'
import { messageLabel } from '../../utils/labels'

const account = ref('')
const password = ref('')
const passwordVisible = ref(false)
const submitting = ref(false)
const checkingSession = ref(false)
const savedAccountFilled = ref(false)

const canSubmit = computed(() => account.value.length > 0 && password.value.length > 0)

onLoad(() => {
  restoreLoginForm()
  if (hasToken()) {
    autoLoginWithToken()
    return
  }
})

function restoreLoginForm() {
  account.value = getLastLoginAccount()
  savedAccountFilled.value = Boolean(account.value)
}

function autoLoginWithToken() {
  checkingSession.value = true
  getMe()
    .then((data) => {
      redirectByNextAction(data.next_action)
    })
    .catch(() => {})
    .finally(() => {
      checkingSession.value = false
    })
}

function submit(source = false) {
  if (!canSubmit.value || submitting.value) {
    return
  }

  submitting.value = true
  login(account.value, password.value)
    .then((data) => {
      redirectByNextAction(data.next_action)
    })
    .catch((error) => {
      uni.showToast({ title: messageLabel(error.message), icon: 'none' })
    })
    .finally(() => {
      submitting.value = false
    })
}
</script>

<style scoped>
.login-page {
  padding-top: 112rpx;
}

.brand {
  margin-bottom: 58rpx;
  text-align: center;
}

.brand-title {
  color: #1f2933;
  font-size: 54rpx;
  font-weight: 700;
  letter-spacing: 0;
}

.brand-subtitle {
  margin-top: 14rpx;
  color: #667382;
  font-size: 26rpx;
}

.login-panel {
  padding: 34rpx 30rpx 32rpx;
}

.field + .field {
  margin-top: 28rpx;
}

.password-row {
  display: flex;
  align-items: center;
  min-height: 84rpx;
  border: 1rpx solid #d9e1ea;
  border-radius: 4rpx;
  background: #ffffff;
}

.password-input {
  flex: 1;
  min-width: 0;
  padding: 0 22rpx;
  color: #1f2933;
  font-size: 28rpx;
}

.password-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 104rpx;
  height: 84rpx;
  line-height: 84rpx;
  background: transparent;
  color: #285b8f;
  font-size: 25rpx;
}

.login-button {
  width: 100%;
  margin-top: 28rpx;
}

.security-note {
  margin-top: 20rpx;
  color: #7a8796;
  font-size: 22rpx;
  line-height: 1.5;
}

.login-options {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 22rpx;
  color: #6b7785;
  font-size: 24rpx;
  line-height: 1.5;
}

.option-list {
  margin-top: 18rpx;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  color: #2b3642;
  font-size: 25rpx;
  line-height: 1.5;
}

.option-row.disabled {
  color: #98a4b2;
}
</style>
