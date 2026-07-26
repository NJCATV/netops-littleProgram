<template>
  <view class="page logs-page">
    <view class="compact-bar">
      <view>
        <view class="bar-title">日志查看</view>
        <view class="bar-subtitle">共 {{ total }} 条</view>
      </view>
      <view class="switch-row">
        <button class="switch-button" :class="{ active: logType === 'operation' }" @tap="switchType('operation')">操作</button>
        <button class="switch-button" :class="{ active: logType === 'login' }" @tap="switchType('login')">登录</button>
      </view>
    </view>

    <view class="search-row">
      <input
        v-model.trim="keyword"
        class="search-input"
        placeholder="人员 / 手机 / IP / 动作 / 详情"
        placeholder-class="placeholder"
        confirm-type="search"
        @confirm="loadLogs"
      />
      <button class="search-button" @tap="loadLogs">搜索</button>
    </view>

    <view v-if="loading" class="status-text">加载中...</view>
    <view v-else-if="items.length === 0" class="panel empty-panel">暂无日志</view>

    <view v-else class="list">
      <view v-for="item in items" :key="`${item.type}-${item.id}`" class="panel log-card">
        <view class="item-head">
          <view class="item-title">{{ logTitle(item) }}</view>
          <text class="tag" :class="{ danger: item.result === 'fail' }">{{ logBadge(item) }}</text>
        </view>
        <view class="item-meta">{{ actorName(item) }}｜{{ item.created_at }}</view>
        <view class="detail-line">{{ logDetail(item) }}</view>
        <view class="detail-line muted">{{ ipText(item) }}</view>
      </view>
    </view>

    <button v-if="items.length < total" class="secondary-button more-button" :loading="loadingMore" :disabled="loadingMore" @tap="loadMore">
      加载更多
    </button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { listLogs } from '../../../api/adminLogs'
import { requireLogin } from '../../../api/auth'
import { messageLabel, roleLabel } from '../../../utils/labels'

const logType = ref('operation')
const keyword = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const loadingMore = ref(false)

onLoad(() => {
  requireLogin()
    .then(() => loadLogs())
    .catch((error) => {
      if (error.message !== '未登录') {
        toast(error.message)
      }
    })
})

function switchType(type) {
  if (logType.value === type) {
    return
  }
  logType.value = type
  loadLogs()
}

function loadLogs() {
  page.value = 1
  loading.value = true
  return fetchLogs()
    .then((data) => {
      items.value = data.items || []
      total.value = data.total || 0
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      loading.value = false
    })
}

function loadMore() {
  page.value += 1
  loadingMore.value = true
  fetchLogs()
    .then((data) => {
      items.value = items.value.concat(data.items || [])
      total.value = data.total || total.value
    })
    .catch((error) => {
      page.value -= 1
      toast(error.message)
    })
    .finally(() => {
      loadingMore.value = false
    })
}

function fetchLogs() {
  return listLogs({
    type: logType.value,
    keyword: keyword.value,
    page: page.value,
    page_size: 30
  })
}

function actorName(item) {
  const user = item.user || {}
  if (user.real_name) {
    return `${user.real_name} ${user.mobile || ''}`.trim()
  }
  return item.login_account || '系统/未知用户'
}

function logTitle(item) {
  if (item.type === 'login') {
    return item.result === 'success' ? '登录成功' : '登录失败'
  }
  return `${moduleLabel(item.module)} / ${actionLabel(item.action)}`
}

function logBadge(item) {
  if (item.type === 'login') {
    return item.result === 'success' ? '成功' : '失败'
  }
  return item.target_type || '操作'
}

function logDetail(item) {
  if (item.type === 'login') {
    return item.fail_reason ? `失败原因：${messageLabel(item.fail_reason)}` : `角色：${roleLabel((item.user || {}).role_code)}`
  }
  const target = item.target_id ? `${item.target_type || '对象'}#${item.target_id}` : '未记录对象'
  return `${target}｜${item.detail || '--'}`
}

function ipText(item) {
  return `IP：${item.ip || item.login_ip || '--'}`
}

function moduleLabel(module) {
  const map = {
    'admin.orgs': '组织管理',
    'admin.users': '用户管理',
    'admin.menus': '功能管理',
    'admin.servers': '服务器管理',
    auth: '认证',
    files: '文件'
  }
  return map[module] || module || '--'
}

function actionLabel(action) {
  const map = {
    create: '新增',
    update: '编辑',
    active: '启用',
    disabled: '禁用',
    enable: '启用',
    disable: '禁用',
    delete: '删除',
    status: '状态变更',
    credential_create: '新增资料',
    credential_update: '编辑资料',
    credential_delete: '删除资料',
    credential_reveal: '查看资料',
    reset_password: '重置密码',
    bind_oss: '绑定 OSS',
    bind_oss_failed: 'OSS 绑定失败',
    change_password: '修改密码',
    upload_avatar: '上传头像'
  }
  return map[action] || action || '--'
}

function toast(message) {
  uni.showToast({ title: messageLabel(message), icon: 'none' })
}
</script>

<style scoped>
.logs-page {
  padding-bottom: 48rpx;
}

.compact-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.bar-title {
  color: #1f2933;
  font-size: 34rpx;
  font-weight: 700;
}

.bar-subtitle {
  margin-top: 6rpx;
  color: #6b7785;
  font-size: 24rpx;
}

.switch-row {
  display: flex;
  border: 1rpx solid #d8e0e8;
  border-radius: 6rpx;
  overflow: hidden;
  background: #ffffff;
}

.switch-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 64rpx;
  background: #ffffff;
  color: #46617d;
  font-size: 25rpx;
}

.switch-button.active {
  background: #1f6feb;
  color: #ffffff;
}

.search-row {
  display: flex;
  gap: 14rpx;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  min-width: 0;
  min-height: 76rpx;
  padding: 0 20rpx;
  border: 1rpx solid #d9e1ea;
  border-radius: 4rpx;
  background: #ffffff;
  font-size: 26rpx;
}

.search-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 118rpx;
  min-height: 76rpx;
  background: #1f6feb;
  color: #ffffff;
  font-size: 25rpx;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.log-card {
  padding: 22rpx;
}

.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.item-title {
  min-width: 0;
  overflow: hidden;
  color: #1f2933;
  font-size: 29rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta,
.detail-line {
  margin-top: 10rpx;
  color: #5b6878;
  font-size: 24rpx;
  line-height: 1.5;
  word-break: break-all;
}

.tag {
  flex: 0 0 auto;
  padding: 6rpx 12rpx;
  border-radius: 4rpx;
  background: #eef4fb;
  color: #285b8f;
  font-size: 22rpx;
}

.tag.danger {
  background: #fff0ef;
  color: #c9352b;
}

.empty-panel {
  padding: 42rpx 26rpx;
  color: #6b7785;
  font-size: 26rpx;
  text-align: center;
}

.more-button {
  width: 100%;
  margin-top: 22rpx;
}
</style>
