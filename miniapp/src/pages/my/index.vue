<template>
  <view class="page my-page">
    <view class="profile-head" @tap="chooseAvatar">
      <image v-if="avatarSrc" class="avatar avatar-image" :src="avatarSrc" mode="aspectFill" />
      <view v-else class="avatar">{{ initial }}</view>
      <view class="profile-main">
        <view class="name">{{ user.real_name || '智维用户' }}</view>
        <view class="meta">{{ user.org_name || '未分配组织' }}｜{{ roleLabel(user.role_code) }}</view>
        <view class="avatar-tip">点击头像区域更换头像</view>
      </view>
    </view>

    <view class="panel info-panel">
      <view class="info-row">
        <text>手机号</text>
        <text>{{ user.mobile || '-' }}</text>
      </view>
      <view class="info-row">
        <text>用户类型</text>
        <text>{{ userTypeLabel(user.user_type) }}</text>
      </view>
      <view class="info-row">
        <text>账号状态</text>
        <text>{{ statusLabel(user.status) }}</text>
      </view>
      <view class="info-row">
        <text>OSS 账号</text>
        <text>{{ user.oss_account || '未绑定' }}</text>
      </view>
      <view class="info-row">
        <text>OSS 状态</text>
        <text>{{ ossStatusLabel(user.oss_bind_status) }}</text>
      </view>
      <view v-if="user.manage_org_name" class="info-row">
        <text>管理范围</text>
        <text>{{ user.manage_org_name }}</text>
      </view>
    </view>

    <view class="panel action-panel">
      <view class="action-row" @tap="goChangePassword">
        <text>修改密码</text>
        <text class="chevron">›</text>
      </view>
      <view class="action-row" @tap="chooseAvatar">
        <text>更换头像</text>
        <text class="chevron">›</text>
      </view>
      <view class="action-row" @tap="goBindOss">
        <text>OSS 账号确认或更新</text>
        <text class="chevron">›</text>
      </view>
      <view class="action-row danger-text" @tap="onLogout">
        <text>退出登录</text>
        <text>退出</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getStoredUser, logout, requireLogin, resolveAssetUrl, uploadAvatar } from '../../api/auth'
import { messageLabel, ossStatusLabel, roleLabel, statusLabel, userTypeLabel } from '../../utils/labels'

const user = ref(getStoredUser())
const initial = computed(() => (user.value.real_name || '用').slice(0, 1))
const avatarSrc = computed(() => resolveAssetUrl(user.value.avatar_url))

onShow(() => {
  requireLogin()
    .then((data) => {
      user.value = data.user || getStoredUser()
    })
    .catch((error) => {
      if (error.message !== '未登录') {
        uni.showToast({ title: messageLabel(error.message), icon: 'none' })
      }
    })
})

function goChangePassword() {
  uni.navigateTo({ url: '/pages/auth/change-password/index' })
}

function goBindOss() {
  uni.navigateTo({ url: '/pages/auth/bind-oss/index' })
}

function chooseAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success(result) {
      const filePath = result.tempFilePaths && result.tempFilePaths[0]
      if (!filePath) {
        return
      }
      uni.showLoading({ title: '上传中' })
      uploadAvatar(filePath)
        .then((data) => {
          user.value = data.user || getStoredUser()
          uni.hideLoading()
          uni.showToast({ title: '头像已更新', icon: 'success' })
        })
        .catch((error) => {
          uni.hideLoading()
          uni.showToast({ title: messageLabel(error.message), icon: 'none' })
        })
    }
  })
}

function onLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确认退出当前账号？',
    success(result) {
      if (!result.confirm) {
        return
      }
      logout().finally(() => {
        uni.reLaunch({ url: '/pages/login/index' })
      })
    }
  })
}
</script>

<style scoped>
.profile-head {
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 34rpx 28rpx;
  border-radius: 8rpx;
  background: #2f3b4a;
  color: #ffffff;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 86rpx;
  height: 86rpx;
  border-radius: 50%;
  background: #1f6feb;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
}

.avatar-image {
  display: block;
}

.profile-main {
  min-width: 0;
}

.name {
  overflow: hidden;
  font-size: 34rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.75);
  font-size: 24rpx;
}

.avatar-tip {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.55);
  font-size: 22rpx;
}

.info-panel,
.action-panel {
  margin-top: 22rpx;
  overflow: hidden;
}

.info-row,
.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 88rpx;
  padding: 0 24rpx;
  border-bottom: 1rpx solid #edf1f5;
  color: #2b3642;
  font-size: 26rpx;
}

.info-row:last-child,
.action-row:last-child {
  border-bottom: 0;
}

.info-row text:last-child {
  max-width: 430rpx;
  overflow: hidden;
  color: #6b7785;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  color: #8a96a6;
  font-size: 42rpx;
}
</style>
