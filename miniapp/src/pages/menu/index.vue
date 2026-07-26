<template>
  <view class="page menu-page">
    <view class="top-band">
      <view class="user-line">
        <image v-if="avatarSrc" class="avatar avatar-image" :src="avatarSrc" mode="aspectFill" />
        <view v-else class="avatar">{{ initial }}</view>
        <view class="user-copy">
          <view class="user-name">{{ user.real_name || '智维用户' }}</view>
          <view class="user-meta">{{ user.org_name || '未分配组织' }}｜{{ roleLabel(user.role_code) }}</view>
        </view>
      </view>
    </view>

    <view v-if="loading" class="status-text">加载中...</view>

    <view v-else-if="groups.length === 0" class="panel empty-panel">
      <view class="empty-title">暂无可用功能</view>
      <view class="empty-desc">请联系管理员确认菜单权限。</view>
    </view>

    <view v-else class="group-list">
      <view v-for="group in groups" :key="group.group_name" class="menu-section">
        <view class="section-title">{{ group.group_name }}</view>
        <view class="menu-grid">
          <view v-for="item in group.items" :key="item.menu_key" class="menu-item" @tap="openApp(item)">
            <view class="menu-icon" :class="iconClass(item.icon)">{{ iconText(item.icon) }}</view>
            <view class="menu-name">{{ item.name }}</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getStoredUser, requireLogin, resolveAssetUrl } from '../../api/auth'
import { listApps } from '../../api/menu'
import { messageLabel, roleLabel } from '../../utils/labels'

const user = ref(getStoredUser())
const groups = ref([])
const loading = ref(false)

const initial = computed(() => (user.value.real_name || '用').slice(0, 1))
const avatarSrc = computed(() => resolveAssetUrl(user.value.avatar_url))

onShow(() => {
  loadPage()
})

function loadPage() {
  loading.value = true
  requireLogin()
    .then((data) => {
      user.value = data.user || getStoredUser()
      return listApps()
    })
    .then((data) => {
      const backendGroups = data.groups || []
      if (backendGroups.length) {
        groups.value = backendGroups
        return
      }

      groups.value = groupItems(data.items || [])
    })
    .catch((error) => {
      if (error.message !== '未登录') {
        uni.showToast({ title: messageLabel(error.message), icon: 'none' })
      }
    })
    .finally(() => {
      loading.value = false
    })
}

function groupItems(items) {
  const map = {}
  items.forEach((item) => {
    const groupName = item.group_name || '全部功能'
    if (!map[groupName]) {
      map[groupName] = []
    }
    map[groupName].push(item)
  })
  return Object.keys(map).map((groupName) => ({ group_name: groupName, items: map[groupName] }))
}

function openApp(item) {
  if (!item.path) {
    uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })
    return
  }

  if (item.path === '/pages/menu/index' || item.path === '/pages/my/index') {
    uni.switchTab({ url: item.path })
    return
  }

  uni.navigateTo({
    url: item.path,
    fail() {
      uni.showToast({ title: '页面待迁移', icon: 'none' })
    }
  })
}

function iconText(icon) {
  const map = {
    camera: '拍',
    calculator: '算',
    search: '查',
    calendar: '班',
    'folder-search': '档',
    usergroup: '人',
    tree: '组',
    app: '菜',
    log: '志',
    server: '服',
    setting: '设'
  }
  return map[icon] || '用'
}

function iconClass(icon) {
  return `icon-${icon || 'default'}`.replace(/[^a-z0-9_-]/gi, '-')
}
</script>

<style scoped>
.menu-page {
  padding-bottom: 38rpx;
}

.top-band {
  margin: -28rpx -24rpx 28rpx;
  padding: 58rpx 32rpx 34rpx;
  background: #2f3b4a;
  color: #ffffff;
}

.user-line {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: #1f6feb;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
}

.avatar-image {
  display: block;
}

.user-copy {
  min-width: 0;
}

.user-name {
  overflow: hidden;
  font-size: 32rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-meta {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.75);
  font-size: 24rpx;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.section-title {
  margin-bottom: 16rpx;
  color: #1f2933;
  font-size: 30rpx;
  font-weight: 700;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18rpx 12rpx;
}

.menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  padding: 18rpx 4rpx;
  border: 1rpx solid #e4e9ef;
  border-radius: 8rpx;
  background: #ffffff;
}

.menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70rpx;
  height: 70rpx;
  border-radius: 8rpx;
  background: #1f6feb;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 700;
}

.icon-camera,
.icon-search {
  background: #16845f;
}

.icon-calculator,
.icon-folder-search {
  background: #6b55d9;
}

.icon-usergroup,
.icon-tree,
.icon-app,
.icon-log,
.icon-setting {
  background: #b45f06;
}

.menu-name {
  width: 100%;
  margin-top: 12rpx;
  overflow: hidden;
  color: #2b3642;
  font-size: 24rpx;
  line-height: 1.3;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-panel {
  padding: 44rpx 28rpx;
}

.empty-title {
  color: #1f2933;
  font-size: 30rpx;
  font-weight: 700;
}

.empty-desc {
  margin-top: 12rpx;
  color: #6b7785;
  font-size: 25rpx;
}
</style>
