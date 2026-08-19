<template>
  <view class="page my-page">
    <view class="profile-head" @tap="chooseAvatar">
      <image v-if="avatarSrc" class="avatar avatar-image" :src="avatarSrc" mode="aspectFill" @error="onAvatarError" />
      <view v-else class="avatar">{{ initial }}</view>
      <view class="profile-main">
        <view class="name">{{ user.real_name || '智维用户' }}</view>
        <view class="meta">{{ user.org_name || '未分配组织' }}｜{{ roleLabel(user.role_code) }}</view>
        <view class="avatar-tip">点击选择照片并裁切 · 上传不超过 2MB</view>
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
import { syncCustomTabBar } from '../../utils/tab-bar'

const user = ref(getStoredUser())
const avatarLoadFailed = ref(false)
const avatarVersion = ref(Date.now())
const initial = computed(() => (user.value.real_name || '用').slice(0, 1))
const avatarSrc = computed(() => {
  if (avatarLoadFailed.value) return ''
  const url = resolveAssetUrl(user.value.avatar_url)
  if (!url) return ''
  return `${url}${url.includes('?') ? '&' : '?'}v=${avatarVersion.value}`
})

const AVATAR_MAX_BYTES = 2 * 1024 * 1024
const AVATAR_MIN_DIMENSION = 128
const AVATAR_MAX_DIMENSION = 4096
const AVATAR_TYPES = new Set(['jpg', 'jpeg', 'png', 'webp'])

onShow(() => {
  syncCustomTabBar(2)
  avatarLoadFailed.value = false
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
  uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sourceType: ['album', 'camera'],
    async success(result) {
      const selectedFile = result.tempFiles && result.tempFiles[0]
      const filePath = selectedFile?.tempFilePath || selectedFile?.path
      if (!filePath) {
        return
      }
      uni.showLoading({ title: '准备裁切' })
      let uploadPath = ''
      try {
        const croppedPath = await cropAvatar(filePath)
        uploadPath = await compressAvatar(croppedPath)
        await validateAvatar(uploadPath)
      } catch (error) {
        uni.hideLoading()
        if (!error.cancelled) uni.showToast({ title: error.message, icon: 'none' })
        return
      }
      uni.hideLoading()
      uni.showLoading({ title: '上传中' })
      uploadAvatar(uploadPath)
        .then((data) => {
          user.value = data.user || getStoredUser()
          avatarLoadFailed.value = false
          avatarVersion.value = Date.now()
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

function cropAvatar(filePath) {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    if (typeof wx !== 'undefined' && typeof wx.cropImage === 'function') {
      wx.cropImage({
        src: filePath,
        cropScale: '1:1',
        success: (result) => resolve(result.tempFilePath),
        fail: (error) => {
          const cancelled = /cancel/i.test(error.errMsg || '')
          reject(Object.assign(new Error(cancelled ? '已取消裁切' : '头像裁切失败，请重试'), { cancelled }))
        }
      })
      return
    }
    // #endif
    reject(new Error('当前微信版本不支持头像裁切，请升级微信后重试'))
  })
}

function compressAvatar(filePath) {
  return new Promise((resolve, reject) => {
    uni.compressImage({
      src: filePath,
      quality: 82,
      compressedWidth: 1024,
      compressedHeight: 1024,
      success: (result) => resolve(result.tempFilePath),
      fail: () => reject(new Error('头像处理失败，请重新选择'))
    })
  })
}

function validateAvatar(filePath) {
  return Promise.all([getImageMeta(filePath), getFileSize(filePath)]).then(([info, size]) => {
    const width = Number(info.width || 0)
    const height = Number(info.height || 0)
    const type = String(info.type || '').toLowerCase()
    if (type && !AVATAR_TYPES.has(type)) throw new Error('仅支持 JPG、PNG 或 WebP')
    if (Number(size) > AVATAR_MAX_BYTES) throw new Error('头像处理后仍超过 2MB，请换一张照片')
    if (width < AVATAR_MIN_DIMENSION || height < AVATAR_MIN_DIMENSION) throw new Error('头像宽高不能小于 128 像素')
    if (width > AVATAR_MAX_DIMENSION || height > AVATAR_MAX_DIMENSION) throw new Error('头像宽高不能超过 4096 像素')
    if (width !== height) throw new Error('请将头像裁切为正方形')
  })
}

function getImageMeta(filePath) {
  return new Promise((resolve, reject) => uni.getImageInfo({ src: filePath, success: resolve, fail: () => reject(new Error('无法读取图片，请重新选择')) }))
}

function getFileSize(filePath) {
  return new Promise((resolve, reject) => uni.getFileInfo({ filePath, success: (result) => resolve(result.size), fail: () => reject(new Error('无法读取图片大小，请重新选择')) }))
}

function onAvatarError() {
  if (avatarLoadFailed.value) return
  avatarLoadFailed.value = true
  uni.showToast({ title: '头像加载失败，请重新上传', icon: 'none' })
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

.my-page {
  padding-bottom: 150rpx;
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
