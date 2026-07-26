<template>
  <view class="page">
    <view class="panel form-card">
      <view class="page-title">OSS 账号确认</view>
      <view class="field">
        <view class="field-label">OSS 账号</view>
        <input v-model.trim="ossAccount" class="input" placeholder="请输入 OSS 账号" placeholder-class="placeholder" />
      </view>
      <view class="field">
        <view class="field-label">OSS 密码</view>
        <input v-model="ossPassword" class="input" password placeholder="请输入 OSS 密码" placeholder-class="placeholder" />
      </view>
      <checkbox-group @change="onPasswordOptionChange">
        <label class="checkbox-row">
          <checkbox value="yes" :checked="useOssPasswordForLogin" color="#1f6feb" />
          <text>使用 OSS 密码作为小程序登录密码</text>
        </label>
      </checkbox-group>
      <button class="primary-button submit-button" :loading="submitting" :disabled="submitting" @tap="submit">确认并继续</button>
      <button class="secondary-button skip-button" :disabled="submitting" @tap="skipBind">暂不绑定，进入系统</button>
      <view class="hint-text">OSS 账号可以稍后在“我的”页面绑定。未绑定时，每次重新打开小程序会提醒一次。</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { bindOss, getStoredUser, redirectByNextAction } from '../../../api/auth'
import { messageLabel } from '../../../utils/labels'

const ossAccount = ref('')
const ossPassword = ref('')
const useOssPasswordForLogin = ref(false)
const submitting = ref(false)

onLoad(() => {
  const user = getStoredUser()
  ossAccount.value = user.oss_account || ''
})

function submit() {
  if (!ossAccount.value || !ossPassword.value) {
    uni.showToast({ title: '请填写 OSS 账号和密码', icon: 'none' })
    return
  }

  submitting.value = true
  bindOss(ossAccount.value, ossPassword.value, useOssPasswordForLogin.value)
    .then((data) => {
      uni.showToast({ title: 'OSS 账号已确认', icon: 'success' })
      redirectByNextAction(data.next_action)
    })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => {
      submitting.value = false
    })
}

function onPasswordOptionChange(event) {
  useOssPasswordForLogin.value = (event.detail.value || []).includes('yes')
}

function skipBind() {
  uni.setStorageSync('oss_reminder_skipped', true)
  uni.switchTab({ url: '/pages/workbench/index' })
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

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 24rpx;
  color: #2b3642;
  font-size: 26rpx;
  line-height: 1.5;
}

.submit-button {
  width: 100%;
  margin-top: 34rpx;
}

.skip-button {
  width: 100%;
  margin-top: 18rpx;
}

.hint-text {
  margin-top: 18rpx;
  color: #6b7785;
  font-size: 24rpx;
  line-height: 1.6;
}
</style>
