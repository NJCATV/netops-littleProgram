<template>
  <view class="page workbench-page">
    <view class="hero">
      <view class="hero-title-row">
        <view><view class="hero-title">智维工作台</view><view class="hero-subtitle">网络运维与现场工具统一入口</view></view>
        <view class="status-pill"><i /> 在线</view>
      </view>
      <view class="profile-card">
        <image v-if="avatar" class="avatar" :src="avatar" mode="aspectFill" @error="avatarLoadFailed = true" />
        <view v-else class="avatar avatar-text">{{ initial }}</view>
        <view class="identity"><view class="welcome">欢迎回来</view><view class="name">{{ user.real_name || '智维用户' }}</view><view class="meta">{{ user.org_name || '未分配组织' }} · {{ roleLabel(user.role_code) }}</view></view>
      </view>
    </view>

    <view class="menu-search"><text class="search-mark">⌕</text><input v-model.trim="keyword" placeholder="搜索功能" placeholder-class="search-placeholder" /><text v-if="keyword" class="search-clear" @tap="keyword = ''">×</text></view>
    <view v-if="loading && !groups.length" class="hint">正在加载功能菜单…</view>
    <view v-else-if="!visibleGroups.length" class="empty">{{ keyword ? '没有匹配的功能' : '暂无可用功能，请联系管理员确认菜单权限。' }}</view>

    <view v-else class="groups">
      <view v-for="group in visibleGroups" :key="group.group_name" class="group-card">
        <view class="group-head"><view class="group-name">{{ group.group_name }}</view><view class="group-count">{{ group.items.length }} 项</view></view>
        <view class="grid">
          <view v-for="item in group.items" :key="item.menu_key" class="entry" @tap="go(item)">
            <view class="entry-icon" :class="`icon-${iconFor(item)}`">{{ iconText(iconFor(item)) }}</view><view class="entry-name">{{ item.name }}</view>
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
import { syncCustomTabBar } from '../../utils/tab-bar'

const routeMap = {
  '/dashboard': '/pages/netops/dashboard/index', '/onu-search': '/pages/netops/onu/index', '/quality': '/pages/netops/quality/index', '/performance': '/pages/netops/performance/index',
  '/collector': '/pages/netops/collector/index', '/devices': '/pages/netops/devices/index', '/probe': '/pages/netops/devices/index', '/hfc': '/pages/netops/hfc/index', '/cm-search': '/pages/netops/hfc/index', '/cmts-devices': '/pages/netops/hfc/index',
  '/radius': '/pages/netops/radius/index', '/radius/search': '/pages/netops/radius/index', '/aiops': '/pages/netops/aiops/index', '/aiops/board': '/pages/netops/aiops/index', '/aiops/knowledge': '/pages/netops/aiops-knowledge/index', '/aiops/admin': '/pages/netops/aiops-admin/index',
  '/ai-assistant': '/pages/netops/ai-assistant/index', '/boss-users': '/pages/netops/boss-users/index', '/settings': '/pages/netops/admin/index', '/device-orgs': '/pages/netops/admin/index', '/permissions': '/pages/admin/menus/index', '/users': '/pages/admin/users/index', '/user-orgs': '/pages/admin/orgs/index',
  '/system-audit': '/pages/netops/system-audit/index', '/infrastructure': '/pages/netops/infrastructure/index', '/work-orders': '/pages/work-orders/index'
}
const keyMap = {
  'netops.dashboard': '/pages/netops/dashboard/index', 'netops.onu': '/pages/netops/onu/index', 'netops.onu_search': '/pages/netops/onu/index', 'netops.quality': '/pages/netops/quality/index', 'netops.performance': '/pages/netops/performance/index', 'netops.collector': '/pages/netops/collector/index',
  'netops.devices': '/pages/netops/devices/index', 'netops.hfc': '/pages/netops/hfc/index', 'netops.cmts_devices': '/pages/netops/hfc/index', 'netops.radius': '/pages/netops/radius/index', 'netops.aiops': '/pages/netops/aiops/index', 'netops.aiops_knowledge': '/pages/netops/aiops-knowledge/index',
  'netops.aiops_admin': '/pages/netops/aiops-admin/index', 'netops.system_audit': '/pages/netops/system-audit/index', 'netops.infrastructure': '/pages/netops/infrastructure/index', 'netops.ai_assistant': '/pages/netops/ai-assistant/index',
  'netops.boss-users': '/pages/netops/boss-users/index', 'netops.boss_users': '/pages/netops/boss-users/index', 'netops.admin': '/pages/netops/admin/index', 'netops.work_orders': '/pages/work-orders/index'
}
const nameMap = {
  '统一驾驶舱': '/pages/netops/dashboard/index', '网络总览': '/pages/netops/dashboard/index', '单台ONU查询': '/pages/netops/onu/index', 'ONU查询': '/pages/netops/onu/index', 'ONU质差管理': '/pages/netops/quality/index', 'OLT性能看板': '/pages/netops/performance/index',
  '采集监控': '/pages/netops/collector/index', 'OLT设备管理': '/pages/netops/devices/index', 'CMCMTS查询': '/pages/netops/hfc/index', 'CMMAC查询': '/pages/netops/hfc/index', 'CMTS设备管理': '/pages/netops/hfc/index', 'Radius管理系统': '/pages/netops/radius/index', 'Radius一键查询': '/pages/netops/radius/index',
  'AIOps运维看板': '/pages/netops/aiops/index', 'AIOps运维中心': '/pages/netops/aiops/index', 'AIOps知识库': '/pages/netops/aiops-knowledge/index', '知识库': '/pages/netops/aiops-knowledge/index', 'AIOps系统管理': '/pages/netops/aiops-admin/index',
  '系统审计与使用分析': '/pages/netops/system-audit/index', '基础设施监控': '/pages/netops/infrastructure/index', 'AI问答': '/pages/netops/ai-assistant/index', 'AI运维助手': '/pages/netops/ai-assistant/index', 'BOSS用户管理': '/pages/netops/boss-users/index',
  '设备组织管理': '/pages/netops/admin/index', '网管配置': '/pages/netops/admin/index', '系统配置': '/pages/netops/admin/index', '权限管理': '/pages/admin/menus/index', '用户管理': '/pages/admin/users/index', '用户组织管理': '/pages/admin/orgs/index'
}
const routeIcon = {
  '/pages/netops/dashboard/index': 'dashboard', '/pages/netops/onu/index': 'onu', '/pages/netops/quality/index': 'quality', '/pages/netops/performance/index': 'performance', '/pages/netops/collector/index': 'collector', '/pages/netops/devices/index': 'devices', '/pages/netops/hfc/index': 'hfc', '/pages/netops/radius/index': 'radius',
  '/pages/netops/aiops/index': 'aiops', '/pages/netops/aiops-knowledge/index': 'knowledge', '/pages/netops/aiops-admin/index': 'aiadmin', '/pages/netops/system-audit/index': 'audit', '/pages/netops/infrastructure/index': 'infrastructure', '/pages/netops/ai-assistant/index': 'assistant',
  '/pages/netops/boss-users/index': 'boss', '/pages/netops/admin/index': 'admin', '/pages/work-orders/index': 'workorder'
}
const queryOrder = ['/pages/netops/onu/index', '/pages/netops/hfc/index', '/pages/netops/radius/index']
const monitorOrder = ['/pages/netops/dashboard/index', '/pages/netops/aiops/index', '/pages/netops/quality/index', '/pages/netops/performance/index', '/pages/netops/collector/index']
const netSystemOrder = ['/pages/netops/devices/index', '/pages/netops/boss-users/index', '/pages/netops/admin/index', '/pages/netops/aiops-admin/index', '/pages/netops/system-audit/index', '/pages/netops/infrastructure/index', '/pages/netops/aiops-knowledge/index']
const workOrderPath = '/pages/work-orders/index'
const fieldKeys = new Set(['watermark.camera', 'ip.calculator', 'duty.view', 'server.manage', 'data.query'])
const platformKeys = new Set(['user.manage', 'org.manage', 'menu.manage', 'log.view', 'system.setting'])
const nameOverrides = {
  [workOrderPath]: '智能装维', '/pages/netops/onu/index': 'FTTH 查询', '/pages/netops/hfc/index': 'CM / CMTS 查询', '/pages/netops/dashboard/index': '网络总览', '/pages/netops/quality/index': '质差管理', '/pages/netops/radius/index': 'Radius 查询',
  '/pages/netops/aiops/index': 'AIOps 看板', '/pages/netops/aiops-knowledge/index': 'AIOps 知识库', '/pages/netops/aiops-admin/index': 'AIOps 系统管理', '/pages/netops/system-audit/index': '系统审计', '/pages/netops/infrastructure/index': '基础设施监控',
  '/pages/netops/performance/index': 'OLT 性能', '/pages/netops/collector/index': '采集监控', '/pages/netops/devices/index': 'OLT 设备', '/pages/netops/boss-users/index': 'BOSS 用户', '/pages/netops/admin/index': '网管配置'
}
const iconLabels = { workorder: '装', dashboard: '览', onu: '光', quality: '质', performance: '性', collector: '采', radius: '拨', aiops: '智', assistant: 'AI', knowledge: '库', aiadmin: '控', audit: '审', infrastructure: '服', devices: '网', hfc: '缆', boss: '客', admin: '设', camera: '拍', calculator: '算', search: '查', calendar: '班', 'folder-search': '档', usergroup: '人', tree: '组', app: '权', log: '志', server: '服', setting: '设', default: '用' }

const user = ref(getStoredUser()); const groups = ref([]); const keyword = ref(''); const loading = ref(false); const avatarLoadFailed = ref(false)
const initial = computed(() => (user.value.real_name || '用').slice(0, 1)); const avatar = computed(() => avatarLoadFailed.value ? '' : resolveAssetUrl(user.value.avatar_url))
const visibleGroups = computed(() => { const term = keyword.value.toLowerCase(); if (!term) return groups.value; return groups.value.map((group) => ({ ...group, items: group.items.filter((item) => `${item.name} ${item.menu_key}`.toLowerCase().includes(term)) })).filter((group) => group.items.length) })
onShow(() => { syncCustomTabBar(0); load() })

function load() {
  avatarLoadFailed.value = false
  groups.value = []
  loading.value = true
  requireLogin().then((data) => { user.value = data.user || getStoredUser(); return listApps() }).then((data) => {
    const items = data.groups?.length ? data.groups.flatMap((group) => group.items || []) : (data.items || [])
    groups.value = organizeGroups(items)
  }).catch((error) => { if (error.message !== '未登录') uni.showToast({ title: messageLabel(error.message), icon: 'none' }) }).finally(() => { loading.value = false })
}
function pathFor(item) { const raw = String(item.path || '').trim(); const bare = raw.split(/[?#]/)[0]; const normalized = bare ? (bare.startsWith('/') ? bare : `/${bare}`) : ''; const name = String(item.name || '').replace(/[\s/（）()_-]/g, ''); return routeMap[normalized] || keyMap[item.menu_key] || nameMap[name] || raw }
function iconFor(item) { return routeIcon[pathFor(item)] || (iconLabels[item.icon] ? item.icon : 'default') }
function iconText(icon) { return iconLabels[icon] || iconLabels.default }
function organizeGroups(items) {
  const buckets = { construction: [], query: [], monitor: [], netSystem: [], field: [], platform: [], other: [] }; const seen = new Set()
  items.forEach((source) => {
    const item = { ...source }; const path = pathFor(item)
    if (path === '/pages/netops/ai-assistant/index') return
    if (path === '/pages/netops/boss-users/index' && user.value.role_code !== 'super_admin') return
    const key = [...queryOrder, ...monitorOrder, ...netSystemOrder, workOrderPath].includes(path) ? path : (path || item.menu_key || item.name)
    if (!key || seen.has(key)) return
    seen.add(key); item.path = path; item.name = nameOverrides[path] || item.name
    if (path === workOrderPath) {
      buckets.construction.push(item)
    } else if (queryOrder.includes(path)) {
      buckets.query.push(item)
    } else if (monitorOrder.includes(path)) {
      buckets.monitor.push(item)
    } else if (netSystemOrder.includes(path)) {
      buckets.netSystem.push(item)
    } else if (fieldKeys.has(item.menu_key)) {
      buckets.field.push(item)
    } else if (platformKeys.has(item.menu_key) || /manage|admin|setting|log|permission/i.test(`${item.menu_key} ${path}`)) {
      buckets.platform.push(item)
    } else {
      buckets.other.push(item)
    }
  })
  const sortBy = (order) => (a, b) => order.indexOf(pathFor(a)) - order.indexOf(pathFor(b)); buckets.query.sort(sortBy(queryOrder)); buckets.monitor.sort(sortBy(monitorOrder)); buckets.netSystem.sort(sortBy(netSystemOrder))
  const result = []
  if (buckets.construction.length) result.push({ group_name: '施工服务', items: buckets.construction })
  if (buckets.query.length) result.push({ group_name: '业务查询', items: buckets.query })
  if (buckets.monitor.length) result.push({ group_name: '运行监测', items: buckets.monitor })
  if (buckets.netSystem.length) result.push({ group_name: '网管系统', items: buckets.netSystem })
  if (buckets.field.length) result.push({ group_name: '现场工具', items: buckets.field })
  if (buckets.platform.length) result.push({ group_name: '平台管理', items: buckets.platform })
  if (buckets.other.length) result.push({ group_name: '其他功能', items: buckets.other })
  return result
}
function go(item) {
  const path = pathFor(item); if (!path) { uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' }); return }
  if (path === '/pages/workbench/index' || path === '/pages/my/index' || path === '/pages/netops/ai-assistant/index') { uni.switchTab({ url: path }); return }
  uni.navigateTo({ url: path, fail: () => uni.showToast({ title: '入口不可用，请联系管理员', icon: 'none' }) })
}
</script>

<style scoped>
.workbench-page{padding:0 20rpx 150rpx}.hero{margin:0 -20rpx 20rpx;padding:24rpx 24rpx 22rpx;border-radius:0 0 32rpx 32rpx;background:linear-gradient(145deg,#0b2348,#173d76);color:#fff}.hero-title-row{display:flex;align-items:center;justify-content:space-between}.hero-title{font-size:32rpx;font-weight:750;letter-spacing:1rpx}.hero-subtitle{margin-top:5rpx;color:rgba(255,255,255,.62);font-size:19rpx}.status-pill{display:flex;align-items:center;gap:7rpx;padding:8rpx 13rpx;border:1rpx solid rgba(255,255,255,.17);border-radius:99rpx;color:rgba(255,255,255,.78);font-size:18rpx}.status-pill i{width:10rpx;height:10rpx;border-radius:50%;background:#35ce84}.profile-card{display:flex;align-items:center;gap:16rpx;margin-top:20rpx;padding:17rpx 18rpx;border:1rpx solid rgba(255,255,255,.18);border-radius:20rpx;background:rgba(255,255,255,.10);box-shadow:0 12rpx 26rpx rgba(0,17,48,.15)}.avatar{width:68rpx;height:68rpx;flex:none;border-radius:20rpx;background:#176cff}.avatar-text{display:flex;align-items:center;justify-content:center;font-size:27rpx;font-weight:750}.identity{min-width:0}.welcome{color:rgba(255,255,255,.58);font-size:18rpx}.name{margin:2rpx 0;font-size:28rpx;font-weight:750}.meta{overflow:hidden;color:rgba(255,255,255,.72);font-size:19rpx;text-overflow:ellipsis;white-space:nowrap}.menu-search{display:flex;height:72rpx;align-items:center;gap:12rpx;margin-bottom:18rpx;padding:0 18rpx;border:1rpx solid #dfe6ef;border-radius:18rpx;background:#fff;box-shadow:0 6rpx 18rpx rgba(31,59,92,.05)}.menu-search input{min-width:0;flex:1;color:#25364a;font-size:23rpx}.search-mark{color:#2a65ad;font-size:35rpx;transform:rotate(-20deg)}.search-clear{padding:8rpx;color:#99a4b0;font-size:31rpx}.search-placeholder{color:#97a2af}.groups{display:flex;flex-direction:column;gap:17rpx}.group-card{padding:17rpx 15rpx;border:1rpx solid #e1e8f0;border-radius:21rpx;background:#fff;box-shadow:0 7rpx 22rpx rgba(31,59,92,.035)}.group-head{display:flex;align-items:center;justify-content:space-between;padding:0 3rpx 13rpx}.group-name{color:#1d2c40;font-size:27rpx;font-weight:750}.group-count{color:#919cab;font-size:19rpx}.hint,.empty{padding:50rpx 0;color:#8793a2;font-size:22rpx;text-align:center}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10rpx 8rpx}.entry{position:relative;min-width:0;min-height:118rpx;padding:11rpx 2rpx 8rpx;border-radius:16rpx;background:#f7f9fc;text-align:center}.entry-icon{display:flex;width:62rpx;height:62rpx;margin:0 auto;align-items:center;justify-content:center;border-radius:18rpx;background:linear-gradient(145deg,#0c6bf2,#2454c6);box-shadow:0 7rpx 14rpx rgba(32,98,200,.18);color:#fff;font-size:23rpx;font-weight:750}.icon-quality,.icon-collector{background:linear-gradient(145deg,#e19b36,#bd6814)}.icon-hfc,.icon-aiops,.icon-knowledge{background:linear-gradient(145deg,#7964db,#5843bd)}.icon-radius{background:linear-gradient(145deg,#26978e,#17746f)}.icon-aiadmin,.icon-audit,.icon-infrastructure,.icon-admin,.icon-devices,.icon-boss{background:linear-gradient(145deg,#3177c9,#22559a)}.icon-camera,.icon-search{background:linear-gradient(145deg,#27a478,#157b58)}.icon-calculator,.icon-folder-search{background:linear-gradient(145deg,#7861dd,#5943bd)}.icon-workorder{background:linear-gradient(145deg,#1b84e8,#2452c8)}.entry-name{overflow:hidden;margin-top:7rpx;color:#344255;font-size:19rpx;line-height:1.3;text-overflow:ellipsis;white-space:nowrap}
</style>
