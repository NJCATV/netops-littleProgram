<template>
  <view class="page detail-page">
    <view v-if="loading" class="state">正在加载工单…</view>
    <template v-else-if="order.id">
      <view class="summary">
        <view class="summary-head"><text class="order-no">{{ order.order_no }}</text><text class="status">{{ statusLabel(order.status) }}</text></view>
        <view class="title">{{ order.title || '智能装维工单' }}</view>
        <view class="source">{{ order.source_system === 'OSS' ? '来源：公单通' : '来源：智维平台' }}</view>
      </view>
      <view class="card">
        <view class="card-title">客户信息</view>
        <view class="row"><text>客户</text><text>{{ order.customer_name || '—' }}</text></view>
        <view class="row"><text>联系电话</text><text>{{ order.customer_phone || '—' }}</text></view>
        <view class="row"><text>业务号码</text><text>{{ order.service_no || '—' }}</text></view>
        <view class="row address"><text>安装地址</text><text>{{ order.address_text || '—' }}</text></view>
      </view>
      <view class="card">
        <view class="card-title">办理信息</view>
        <view class="row"><text>处理人</text><text>{{ order.assignee_name || '待领取' }}</text></view>
        <view class="row"><text>所属组织</text><text>{{ order.owner_org_name || '—' }}</text></view>
        <view class="row"><text>更新时间</text><text>{{ formatTime(order.updated_at) }}</text></view>
      </view>
      <view v-if="order.installation" class="card install-card">
        <view class="card-title">现场检测</view>
        <view class="install-status"><text>{{ installationLabel(order.installation.status) }}</text><text v-if="order.installation.final_score !== null && order.installation.final_score !== undefined">{{ Number(order.installation.final_score).toFixed(1) }} 分</text></view>
        <view class="progress"><view class="progress-inner" :style="{ width: `${passedCount * 20}%` }" /></view>
        <view class="progress-text">五项检测已通过 {{ passedCount }}/5</view>
      </view>
      <view class="actions">
        <button v-if="order.status === 'new'" class="secondary" :loading="acting" @tap="action('accept')">接单</button>
        <button v-if="order.status === 'accepted'" class="secondary" :loading="acting" @tap="action('start')">开始处理</button>
        <button v-if="canInstall" class="primary" @tap="openInstallation">进入智能装维</button>
      </view>
    </template>
    <view v-else class="state">未找到该工单</view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getWorkOrder, runWorkOrderAction, startInstallation } from '../../api/workOrders'

const orderId = ref('')
const order = ref({})
const loading = ref(false)
const acting = ref(false)
const currentAttempt = computed(() => order.value.installation?.attempts?.[0] || null)
const passedCount = computed(() => {
  const latest = {}
  ;(currentAttempt.value?.ai_runs || []).forEach((run) => { if (!(run.agent_code in latest)) latest[run.agent_code] = run })
  return Object.values(latest).filter((run) => run.status === 'success' && run.passed === true).length
})
const canInstall = computed(() => ['accepted', 'processing', 'paused', 'completed'].includes(order.value.status))

onLoad((query) => { orderId.value = query.id || '' })
onShow(load)

async function load() {
  if (!orderId.value) return
  loading.value = true
  try { order.value = await getWorkOrder(orderId.value) }
  catch (error) { uni.showToast({ title: error.message || '工单加载失败', icon: 'none' }) }
  finally { loading.value = false }
}
async function action(name) {
  if (acting.value) return
  acting.value = true
  try { await runWorkOrderAction(orderId.value, name); await load(); uni.showToast({ title: name === 'accept' ? '接单成功' : '已开始处理', icon: 'success' }) }
  catch (error) { uni.showToast({ title: error.message || '操作失败', icon: 'none' }) }
  finally { acting.value = false }
}
async function openInstallation() {
  try {
    const installation = order.value.installation
    if (!installation || !installation.attempts?.length || installation.status === 'rejected') await startInstallation(orderId.value)
    uni.navigateTo({ url: `/pages/work-orders/installation?id=${orderId.value}` })
  } catch (error) { uni.showToast({ title: error.message || '无法开始智能装维', icon: 'none' }) }
}
function statusLabel(status) { return ({ new: '待接单', accepted: '已接单', processing: '处理中', paused: '已暂停', completed: '已完成', closed: '已关闭', cancelled: '已取消' })[status] || status || '未知' }
function installationLabel(status) { return ({ draft: '现场采集中', evaluating: '智能检测中', awaiting_signature: '检测通过，待签字', rejected: '检测未通过', completed: '装维已完成' })[status] || status || '未开始' }
function formatTime(value) { return value ? String(value).replace('T', ' ').slice(0, 16) : '—' }
</script>

<style scoped>
.detail-page{padding-bottom:120rpx}.state{padding:100rpx 0;color:#7a8796;text-align:center}.summary{margin:-24rpx -24rpx 22rpx;padding:34rpx 28rpx;background:linear-gradient(145deg,#203147,#2d6597);color:#fff}.summary-head,.row,.install-status{display:flex;justify-content:space-between;gap:24rpx}.order-no,.source{color:rgba(255,255,255,.72);font-size:23rpx}.status{padding:5rpx 14rpx;border-radius:20rpx;background:rgba(255,255,255,.14);font-size:22rpx}.title{margin:17rpx 0 10rpx;font-size:34rpx;font-weight:700}.card{margin-top:18rpx;padding:24rpx;border:1rpx solid #e2e8ef;border-radius:18rpx;background:#fff}.card-title{margin-bottom:16rpx;color:#1c2939;font-size:28rpx;font-weight:700}.row{padding:12rpx 0;color:#657385;font-size:24rpx}.row text:last-child{max-width:68%;color:#263447;text-align:right}.address{align-items:flex-start}.install-status{color:#1f5fae;font-size:24rpx}.progress{overflow:hidden;height:12rpx;margin-top:20rpx;border-radius:8rpx;background:#e5ebf2}.progress-inner{height:100%;background:#2d8a69}.progress-text{margin-top:10rpx;color:#768496;font-size:22rpx}.actions{display:flex;gap:16rpx;margin-top:24rpx}.actions button{flex:1;min-height:82rpx;border-radius:14rpx;font-size:26rpx}.primary{background:#2269c8;color:#fff}.secondary{border:1rpx solid #2b6bb6;background:#fff;color:#225d9d}
</style>
