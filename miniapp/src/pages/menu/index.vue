<template>
  <view class="page menu-page">
    <view class="top-band">
      <view class="user-line">
        <image v-if="avatarSrc" class="avatar avatar-image" :src="avatarSrc" mode="aspectFill" />
        <view v-else class="avatar">{{ initial }}</view>
        <view class="user-copy">
          <view class="hello">欢迎回来</view>
          <view class="user-name">{{ user.real_name || '智维用户' }}</view>
          <view class="user-meta">{{ user.org_name || '未分配组织' }}｜{{ roleLabel(user.role_code) }}</view>
        </view>
      </view>
      <view class="platform-line">
        <view>
          <view class="platform-title">智维工作台</view>
          <view class="platform-sub">工单、网管与现场工具统一入口</view>
        </view>
        <view class="platform-badge">移动运维</view>
      </view>
    </view>

    <view v-if="loading" class="status-text">加载中...</view>

    <view v-else-if="groups.length === 0" class="panel empty-panel">
      <view class="empty-title">暂无可用功能</view>
      <view class="empty-desc">请联系管理员确认菜单权限。</view>
    </view>

    <view v-else class="group-list">
      <view v-for="group in groups" :key="group.group_name" class="menu-section">
        <view class="section-row">
          <view class="section-title">{{ group.group_name }}</view>
          <view class="section-count">{{ group.items.length }} 项</view>
        </view>
        <view class="menu-grid">
          <view v-for="item in group.items" :key="item.menu_key" class="menu-item" @tap="openApp(item)">
            <view class="menu-icon" :class="iconClass(displayIcon(item))">{{ iconText(displayIcon(item)) }}</view>
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

// Production menus are shared with the legacy Web netops platform. Keep its
// route values compatible until all backend menu records use uni-app paths.
const legacyNetopsRoutes = {
  '/dashboard': '/pages/netops/dashboard/index',
  '/onu-search': '/pages/netops/onu/index',
  '/quality': '/pages/netops/quality/index',
  '/performance': '/pages/netops/performance/index',
  '/collector': '/pages/netops/collector/index',
  '/devices': '/pages/netops/devices/index',
  '/probe': '/pages/netops/devices/index',
  '/hfc': '/pages/netops/hfc/index',
  '/cm-search': '/pages/netops/hfc/index',
  '/cmts-devices': '/pages/netops/hfc/index',
  '/boss-users': '/pages/netops/boss-users/index',
  '/settings': '/pages/netops/admin/index',
  '/device-orgs': '/pages/netops/admin/index',
  '/permissions': '/pages/netops/admin/index'
}

const netopsMenuKeys = {
  'netops.dashboard': '/pages/netops/dashboard/index',
  'netops.onu': '/pages/netops/onu/index',
  'netops.quality': '/pages/netops/quality/index',
  'netops.performance': '/pages/netops/performance/index',
  'netops.collector': '/pages/netops/collector/index',
  'netops.devices': '/pages/netops/devices/index',
  'netops.hfc': '/pages/netops/hfc/index',
  'netops.boss-users': '/pages/netops/boss-users/index',
  'netops.admin': '/pages/netops/admin/index'
}

const netopsNames = {
  '统一驾驶舱': '/pages/netops/dashboard/index',
  '网络总览': '/pages/netops/dashboard/index',
  '单台ONU查询': '/pages/netops/onu/index',
  'ONU查询': '/pages/netops/onu/index',
  'ONU质差管理': '/pages/netops/quality/index',
  'OLT性能看板': '/pages/netops/performance/index',
  '采集监控': '/pages/netops/collector/index',
  'OLT设备管理': '/pages/netops/devices/index',
  'CMCMTS查询': '/pages/netops/hfc/index',
  'CMMAC查询': '/pages/netops/hfc/index',
  'CMTS设备管理': '/pages/netops/hfc/index',
  'BOSS用户管理': '/pages/netops/boss-users/index',
  '设备组织管理': '/pages/netops/admin/index',
  '网管配置': '/pages/netops/admin/index',
  '系统配置': '/pages/netops/admin/index',
  '权限管理': '/pages/netops/admin/index'
}

const routeIcons = {
  '/pages/netops/dashboard/index': 'dashboard',
  '/pages/netops/onu/index': 'onu',
  '/pages/netops/quality/index': 'quality',
  '/pages/netops/performance/index': 'performance',
  '/pages/netops/collector/index': 'collector',
  '/pages/netops/devices/index': 'olt',
  '/pages/netops/hfc/index': 'hfc',
  '/pages/netops/boss-users/index': 'customer',
  '/pages/netops/admin/index': 'setting'
}

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
      showOssReminderIfNeeded(user.value)
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

function showOssReminderIfNeeded(currentUser) {
  if (!currentUser || currentUser.oss_bind_status === 'bound' || uni.getStorageSync('oss_reminder_skipped')) {
    return
  }

  uni.showModal({
    title: 'OSS 账号未绑定',
    content: '绑定后可使用 OSS 相关能力。现在可以先进入系统，稍后在“我的”页面绑定。',
    confirmText: '去绑定',
    cancelText: '稍后',
    success(result) {
      uni.setStorageSync('oss_reminder_skipped', true)
      if (result.confirm) {
        uni.navigateTo({ url: '/pages/auth/bind-oss/index' })
      }
    }
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
  const path = resolveMiniappPath(item)
  if (!path) {
    uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })
    return
  }

  if (path === '/pages/workbench/index' || path === '/pages/my/index') {
    uni.switchTab({ url: path })
    return
  }

  uni.navigateTo({
    url: path,
    fail() {
      uni.showToast({ title: '页面暂不可用，请联系管理员', icon: 'none' })
    }
  })
}

function resolveMiniappPath(item) {
  const rawPath = String(item.path || '').trim()
  const route = rawPath.split(/[?#]/)[0]
  const normalizedRoute = route && route.startsWith('/') ? route : route ? `/${route}` : ''
  const normalizedName = String(item.name || '').replace(/[\s/（）()_-]/g, '')

  return legacyNetopsRoutes[normalizedRoute]
    || netopsMenuKeys[item.menu_key]
    || netopsNames[normalizedName]
    || rawPath
}

function displayIcon(item) {
  const icon = String(item.icon || '')
  const knownIcons = ['camera', 'calculator', 'search', 'calendar', 'folder-search', 'usergroup', 'tree', 'app', 'log', 'server', 'setting', 'dashboard', 'onu', 'quality', 'performance', 'collector', 'olt', 'hfc', 'customer', 'organization']
  return knownIcons.includes(icon) ? icon : (routeIcons[resolveMiniappPath(item)] || icon)
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
    setting: '设',
    dashboard: '览',
    onu: '光',
    quality: '质',
    performance: '性',
    collector: '采',
    olt: '网',
    hfc: '缆',
    customer: '客',
    organization: '域'
  }
  return map[icon] || '用'
}

function iconClass(icon) {
  return `icon-${icon || 'default'}`.replace(/[^a-z0-9_-]/gi, '-')
}
</script>

<style scoped>
.menu-page {
  padding-bottom: 46rpx;
}

.top-band {
  margin: -24rpx -24rpx 28rpx;
  padding: 44rpx 32rpx 34rpx;
  border-radius: 0 0 30rpx 30rpx;
  background: linear-gradient(145deg, #203147 0%, #2f4c70 100%);
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

.hello {
  margin-bottom: 2rpx;
  color: rgba(255, 255, 255, 0.62);
  font-size: 21rpx;
}

.user-name {
  overflow: hidden;
  font-size: 34rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-meta {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.75);
  font-size: 24rpx;
}

.platform-line {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20rpx;
  margin-top: 32rpx;
  padding-top: 28rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.13);
}

.platform-title { font-size: 29rpx; font-weight: 700; }
.platform-sub { margin-top: 7rpx; color: rgba(255,255,255,.63); font-size: 22rpx; }
.platform-badge { padding: 9rpx 16rpx; border-radius: 99rpx; background: rgba(255,255,255,.12); color: rgba(255,255,255,.86); font-size: 20rpx; }

.group-list {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.menu-section {
  padding: 24rpx 20rpx 20rpx;
  border: 1rpx solid #e5ebf1;
  border-radius: 20rpx;
  background: #fff;
}

.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.section-count { color: #8793a2; font-size: 21rpx; }

.section-title {
  margin-bottom: 18rpx;
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
  padding: 14rpx 4rpx 10rpx;
  border-radius: 14rpx;
  background: #f8fafc;
}

.menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70rpx;
  height: 70rpx;
  border-radius: 18rpx;
  background: #2d6fbd;
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

.icon-dashboard,
.icon-onu,
.icon-performance,
.icon-olt { background: #2d6fbd; }

.icon-quality,
.icon-collector { background: #c37720; }

.icon-hfc,
.icon-customer { background: #6e58c8; }

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
