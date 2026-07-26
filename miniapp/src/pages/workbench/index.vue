<template>
  <view class="page workbench-page">
    <view class="hero">
      <image v-if="avatar" class="avatar" :src="avatar" mode="aspectFill" />
      <view v-else class="avatar avatar-text">{{ initial }}</view>
      <view class="identity">
        <view class="welcome">欢迎回来</view>
        <view class="name">{{ user.real_name || '智维用户' }}</view>
        <view class="meta">{{ user.org_name || '未分配组织' }}｜{{ roleLabel(user.role_code) }}</view>
      </view>
      <view class="hero-title">智维工作台</view>
      <view class="hero-desc">工单、网管与现场工具统一入口</view>
    </view>

    <view v-if="loading" class="hint">正在加载功能菜单…</view>
    <view v-else-if="!groups.length" class="empty">暂无可用功能，请联系管理员确认菜单权限。</view>

    <view v-else class="groups">
      <view v-for="group in groups" :key="group.group_name" class="group-card">
        <view class="group-head">
          <view class="group-name">{{ group.group_name }}</view>
          <view class="group-count">{{ group.items.length }} 项</view>
        </view>
        <view class="grid">
          <view v-for="item in group.items" :key="item.menu_key" class="entry" @tap="go(item)">
            <view class="entry-icon" :class="`icon-${iconFor(item)}`">{{ iconText(iconFor(item)) }}</view>
            <view class="entry-name">{{ item.name }}</view>
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

const routeMap = {
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
  '/permissions': '/pages/admin/menus/index',
  '/users': '/pages/admin/users/index',
  '/user-orgs': '/pages/admin/orgs/index'
}

const keyMap = {
  'netops.dashboard': '/pages/netops/dashboard/index',
  'netops.onu': '/pages/netops/onu/index',
  'netops.onu_search': '/pages/netops/onu/index',
  'netops.quality': '/pages/netops/quality/index',
  'netops.performance': '/pages/netops/performance/index',
  'netops.collector': '/pages/netops/collector/index',
  'netops.devices': '/pages/netops/devices/index',
  'netops.hfc': '/pages/netops/hfc/index',
  'netops.cmts_devices': '/pages/netops/hfc/index',
  'netops.boss-users': '/pages/netops/boss-users/index',
  'netops.boss_users': '/pages/netops/boss-users/index',
  'netops.admin': '/pages/netops/admin/index'
}

const nameMap = {
  '统一驾驶舱': '/pages/netops/dashboard/index', '网络总览': '/pages/netops/dashboard/index',
  '单台ONU查询': '/pages/netops/onu/index', 'ONU查询': '/pages/netops/onu/index',
  'ONU质差管理': '/pages/netops/quality/index', 'OLT性能看板': '/pages/netops/performance/index',
  '采集监控': '/pages/netops/collector/index', 'OLT设备管理': '/pages/netops/devices/index',
  'CMCMTS查询': '/pages/netops/hfc/index', 'CMMAC查询': '/pages/netops/hfc/index',
  'CMTS设备管理': '/pages/netops/hfc/index', 'BOSS用户管理': '/pages/netops/boss-users/index',
  '设备组织管理': '/pages/netops/admin/index', '网管配置': '/pages/netops/admin/index',
  '系统配置': '/pages/netops/admin/index', '权限管理': '/pages/admin/menus/index',
  '用户管理': '/pages/admin/users/index', '用户组织管理': '/pages/admin/orgs/index'
}

const routeIcon = {
  '/pages/netops/dashboard/index': 'dashboard', '/pages/netops/onu/index': 'onu',
  '/pages/netops/quality/index': 'quality', '/pages/netops/performance/index': 'performance',
  '/pages/netops/collector/index': 'collector', '/pages/netops/devices/index': 'devices',
  '/pages/netops/hfc/index': 'hfc', '/pages/netops/boss-users/index': 'boss',
  '/pages/netops/admin/index': 'admin'
}

const netopsOrder = [
  '/pages/netops/onu/index', '/pages/netops/hfc/index', '/pages/netops/dashboard/index',
  '/pages/netops/quality/index', '/pages/netops/performance/index', '/pages/netops/collector/index',
  '/pages/netops/devices/index', '/pages/netops/boss-users/index', '/pages/netops/admin/index'
]
const convenienceKeys = new Set(['watermark.camera', 'ip.calculator', 'duty.view', 'server.manage'])
const nameOverrides = {
  '/pages/netops/onu/index': 'ONU 查询', '/pages/netops/hfc/index': 'CM / CMTS 查询',
  '/pages/netops/dashboard/index': '网络总览', '/pages/netops/quality/index': '质差管理',
  '/pages/netops/performance/index': 'OLT 性能', '/pages/netops/collector/index': '采集监控',
  '/pages/netops/devices/index': 'OLT 设备', '/pages/netops/boss-users/index': 'BOSS 用户',
  '/pages/netops/admin/index': '网管配置'
}

const iconLabels = {
  dashboard: '览', onu: '光', quality: '质', performance: '性', collector: '采',
  devices: '网', hfc: '缆', boss: '客', admin: '设', camera: '拍', calculator: '算',
  search: '查', calendar: '班', 'folder-search': '档', usergroup: '人', tree: '组',
  app: '菜', log: '志', server: '服', setting: '设', default: '用'
}

const user = ref(getStoredUser())
const groups = ref([])
const loading = ref(false)
const initial = computed(() => (user.value.real_name || '用').slice(0, 1))
const avatar = computed(() => resolveAssetUrl(user.value.avatar_url))

const menuCacheKey = 'workbench_apps_cache_v1'
const cacheTtl = 10 * 60 * 1000
onShow(load)

function load() {
  const cached = uni.getStorageSync(menuCacheKey)
  if (cached && cached.groups && Date.now() - Number(cached.savedAt || 0) < cacheTtl) {
    user.value = getStoredUser() || cached.user || {}
    groups.value = cached.groups
    return
  }
  loading.value = true
  requireLogin()
    .then((data) => {
      user.value = data.user || getStoredUser()
      return listApps()
    })
    .then((data) => {
      const items = data.groups?.length ? data.groups.flatMap((group) => group.items || []) : (data.items || [])
      groups.value = organizeGroups(items)
      uni.setStorageSync(menuCacheKey, { savedAt: Date.now(), user: user.value, groups: groups.value })
    })
    .catch((error) => {
      if (error.message !== '未登录') uni.showToast({ title: messageLabel(error.message), icon: 'none' })
    })
    .finally(() => { loading.value = false })
}

function pathFor(item) {
  const raw = String(item.path || '').trim()
  const bare = raw.split(/[?#]/)[0]
  const normalized = bare ? (bare.startsWith('/') ? bare : `/${bare}`) : ''
  const name = String(item.name || '').replace(/[\s/（）()_-]/g, '')
  return routeMap[normalized] || keyMap[item.menu_key] || nameMap[name] || raw
}

function iconFor(item) {
  const path = pathFor(item)
  return routeIcon[path] || (iconLabels[item.icon] ? item.icon : 'default')
}

function iconText(icon) { return iconLabels[icon] || iconLabels.default }

function organizeGroups(items) {
  const buckets = { netops: [], convenience: [], system: [], other: [] }
  const seen = new Set()
  items.forEach((source) => {
    const item = { ...source }
    const path = pathFor(item)
    if (path === '/pages/netops/boss-users/index' && user.value.role_code !== 'super_admin') return
    const key = netopsOrder.includes(path) ? path : (path || item.menu_key || item.name)
    if (!key || seen.has(key)) return
    seen.add(key)
    item.path = path
    item.name = nameOverrides[path] || item.name
    if (netopsOrder.includes(path)) buckets.netops.push(item)
    else if (convenienceKeys.has(item.menu_key)) buckets.convenience.push(item)
    else if (/manage|admin|setting|log|permission/i.test(`${item.menu_key} ${path}`)) buckets.system.push(item)
    else buckets.other.push(item)
  })
  buckets.netops.sort((a, b) => netopsOrder.indexOf(pathFor(a)) - netopsOrder.indexOf(pathFor(b)))
  const convenienceOrder = ['duty.view', 'server.manage', 'watermark.camera', 'ip.calculator']
  buckets.convenience.sort((a, b) => convenienceOrder.indexOf(a.menu_key) - convenienceOrder.indexOf(b.menu_key))
  const result = []
  if (buckets.netops.length) result.push({ group_name: '网管', items: buckets.netops })
  if (buckets.convenience.length) result.push({ group_name: '便捷工具', items: buckets.convenience })
  if (buckets.system.length) result.push({ group_name: '系统管理', items: buckets.system })
  if (buckets.other.length) result.push({ group_name: '其他功能', items: buckets.other })
  return result
}

function go(item) {
  const path = pathFor(item)
  if (!path) {
    uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })
    return
  }
  if (path === '/pages/workbench/index' || path === '/pages/my/index') {
    uni.switchTab({ url: path })
    return
  }
  uni.navigateTo({ url: path, fail: () => uni.showToast({ title: '入口不可用，请联系管理员', icon: 'none' }) })
}
</script>

<style scoped>
.workbench-page { padding-bottom: 40rpx; }
.hero { position: relative; min-height: 218rpx; margin: -24rpx -24rpx 26rpx; padding: 42rpx 30rpx 28rpx; border-radius: 0 0 30rpx 30rpx; background: linear-gradient(145deg, #203147, #2f4c70); color: #fff; }
.avatar { width: 78rpx; height: 78rpx; border-radius: 50%; background: #1f6feb; }
.avatar-text { display: flex; align-items: center; justify-content: center; font-size: 32rpx; font-weight: 700; }
.identity { position: absolute; top: 42rpx; left: 126rpx; }
.welcome, .meta { color: rgba(255,255,255,.68); font-size: 22rpx; }
.name { margin: 3rpx 0; font-size: 32rpx; font-weight: 700; }
.hero-title { margin-top: 38rpx; padding-top: 24rpx; border-top: 1rpx solid rgba(255,255,255,.15); font-size: 29rpx; font-weight: 700; }
.hero-desc { margin-top: 6rpx; color: rgba(255,255,255,.66); font-size: 22rpx; }
.groups { display: flex; flex-direction: column; gap: 24rpx; }
.group-card { padding: 22rpx 18rpx; border: 1rpx solid #e5ebf1; border-radius: 20rpx; background: #fff; }
.group-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18rpx; }
.group-name { color: #1f2933; font-size: 29rpx; font-weight: 700; }
.group-count, .hint, .empty { color: #8793a2; font-size: 22rpx; }
.hint, .empty { padding: 48rpx 0; text-align: center; }
.grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16rpx 10rpx; }
.entry { min-width: 0; padding: 12rpx 3rpx 8rpx; border-radius: 14rpx; background: #f8fafc; text-align: center; }
.entry-icon { display: flex; align-items: center; justify-content: center; width: 68rpx; height: 68rpx; margin: 0 auto; border-radius: 18rpx; background: #2d6fbd; color: #fff; font-size: 27rpx; font-weight: 700; }
.icon-quality, .icon-collector { background: #c37720; }.icon-hfc, .icon-boss { background: #6e58c8; }.icon-camera, .icon-search { background: #16845f; }.icon-calculator, .icon-folder-search { background: #6b55d9; }.icon-usergroup, .icon-tree, .icon-app, .icon-log, .icon-server, .icon-setting, .icon-admin { background: #b45f06; }
.entry-name { overflow: hidden; margin-top: 9rpx; color: #2b3642; font-size: 22rpx; line-height: 1.3; text-overflow: ellipsis; white-space: nowrap; }
</style>
