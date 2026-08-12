<template>
  <view class="page orders-page">
    <view class="hero">
      <view>
        <view class="hero-title">智能装维</view>
        <view class="hero-desc">公单通工单、现场检测与回单统一处理</view>
      </view>
      <view class="hero-user">{{ user.real_name || '智维用户' }}</view>
    </view>

    <view class="tabs">
      <view :class="['tab', { active: tab === 'mine' }]" @tap="switchTab('mine')">我的工单</view>
      <view :class="['tab', { active: tab === 'todo' }]" @tap="switchTab('todo')">公单通待领取</view>
    </view>

    <view class="search-bar">
      <input v-model.trim="keyword" class="search-input" placeholder="工单号、客户或地址" confirm-type="search" @confirm="load" />
      <button class="search-button" @tap="load">查询</button>
    </view>

    <view v-if="loading" class="status-text">正在加载工单…</view>
    <view v-else-if="!items.length" class="status-text">
      {{ tab === 'todo' && user.oss_bind_status !== 'bound' ? '请先在“我的”页面绑定公单通账号' : '暂无符合条件的工单' }}
    </view>
    <view v-else class="order-list">
      <view v-for="item in items" :key="orderKey(item)" class="order-card" @tap="open(item)">
        <view class="order-head">
          <text class="order-no">{{ orderNo(item) }}</text>
          <text class="status">{{ statusText(item) }}</text>
        </view>
        <view class="order-title">{{ item.title || item.businessName || item.wotype || item.woType || '智能装维工单' }}</view>
        <view class="order-meta">{{ item.customer_name || item.custName || '客户信息待同步' }}</view>
        <view class="order-address">{{ item.address_text || item.situated || '地址信息待同步' }}</view>
        <button v-if="tab === 'todo'" class="claim" :loading="claiming === orderKey(item)" @tap.stop="claim(item)">领取并进入智维工单</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { getStoredUser, requireLogin } from '../../api/auth'
import { claimOssOrder, listOssTodo, listWorkOrders } from '../../api/workOrders'

const user = ref(getStoredUser())
const tab = ref('mine')
const keyword = ref('')
const items = ref([])
const loading = ref(false)
const claiming = ref('')

onShow(() => requireLogin().then((data) => {
  user.value = data.user || getStoredUser()
  load()
}).catch(() => {}))

onPullDownRefresh(() => load().finally(() => uni.stopPullDownRefresh()))

function switchTab(value) {
  if (value === 'todo' && user.value.oss_bind_status !== 'bound') {
    uni.showModal({
      title: '需要公单通账号',
      content: '智能装维直接使用当前智维平台用户已预留的 OSS 绑定信息。是否现在绑定？',
      success(result) {
        if (result.confirm) uni.navigateTo({ url: '/pages/auth/bind-oss/index' })
      }
    })
  }
  tab.value = value
  load()
}

async function load() {
  loading.value = true
  try {
    if (tab.value === 'mine') {
      const data = await listWorkOrders({ keyword: keyword.value, source_system: 'OSS', page: 1, page_size: 50 })
      items.value = data.items || []
    } else if (user.value.oss_bind_status === 'bound') {
      const data = await listOssTodo({ page: 1, rp: 50 })
      const raw = data.items || {}
      const rows = Array.isArray(raw) ? raw : (raw.rows || raw.items || raw.list || [])
      const lowered = keyword.value.toLowerCase()
      items.value = lowered ? rows.filter((item) => JSON.stringify(item).toLowerCase().includes(lowered)) : rows
    } else {
      items.value = []
    }
  } catch (error) {
    items.value = []
    uni.showToast({ title: error.message || '工单加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function orderNo(item) { return item.order_no || item.woNbr || item.external_order_id || '未编号' }
function orderKey(item) { return String(item.id || orderNo(item)) }
function statusText(item) { return item.status || item.runStsDesc || item.runSts || (tab.value === 'todo' ? '待领取' : '待处理') }

function open(item) {
  if (tab.value === 'mine' && item.id) uni.navigateTo({ url: `/pages/work-orders/detail?id=${item.id}` })
}

async function claim(item) {
  const key = orderKey(item)
  if (claiming.value) return
  claiming.value = key
  try {
    const data = await claimOssOrder(item)
    const order = data.work_order || {}
    uni.showToast({ title: '领取成功', icon: 'success' })
    if (order.id) uni.navigateTo({ url: `/pages/work-orders/detail?id=${order.id}` })
    else switchTab('mine')
  } catch (error) {
    uni.showToast({ title: error.message || '领取失败', icon: 'none' })
  } finally {
    claiming.value = ''
  }
}
</script>

<style scoped>
.orders-page { padding-bottom: 80rpx; }
.hero { display:flex; justify-content:space-between; align-items:flex-start; margin:-24rpx -24rpx 24rpx; padding:38rpx 28rpx 34rpx; background:linear-gradient(140deg,#203147,#285b8f); color:#fff; }
.hero-title { font-size:38rpx; font-weight:700; }.hero-desc { margin-top:10rpx; color:rgba(255,255,255,.72); font-size:23rpx; }.hero-user { padding:10rpx 16rpx; border-radius:20rpx; background:rgba(255,255,255,.12); font-size:22rpx; }
.tabs { display:flex; margin-bottom:18rpx; padding:6rpx; border-radius:16rpx; background:#e9eef4; }.tab { flex:1; padding:18rpx 0; color:#637083; text-align:center; }.tab.active { border-radius:12rpx; background:#fff; color:#1f5fae; font-weight:700; box-shadow:0 4rpx 12rpx rgba(28,48,74,.08); }
.order-list { display:flex; flex-direction:column; gap:16rpx; margin-top:20rpx; }.order-card { padding:24rpx; border:1rpx solid #e1e8ef; border-radius:18rpx; background:#fff; }.order-head { display:flex; justify-content:space-between; gap:20rpx; }.order-no { color:#506176; font-size:23rpx; }.status { color:#1768b2; font-size:22rpx; }.order-title { margin-top:14rpx; color:#172133; font-size:30rpx; font-weight:700; }.order-meta,.order-address { margin-top:9rpx; color:#657385; font-size:24rpx; }.claim { margin-top:20rpx; min-height:72rpx; border-radius:12rpx; background:#2269c8; color:#fff; font-size:25rpx; }
</style>
