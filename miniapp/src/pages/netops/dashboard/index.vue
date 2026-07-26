<template>
  <view class="netops-page dashboard-page">
    <view class="hero">
      <view>
        <view class="eyebrow">NETWORK OPERATIONS</view>
        <view class="hero-title">网络运行总览</view>
        <view class="hero-sub">{{ latestText }}</view>
      </view>
      <view class="refresh" @tap="loadData">刷新</view>
    </view>

    <view class="quick-grid">
      <view v-for="item in quickActions" :key="item.path" class="quick-item" @tap="go(item.path)">
        <view class="quick-icon" :class="item.tone">{{ item.icon }}</view>
        <view class="quick-name">{{ item.name }}</view>
      </view>
    </view>

    <view v-if="loading" class="section-card"><view class="status-text">正在汇总网络运行数据...</view></view>
    <template v-else>
      <view class="metric-grid">
        <MetricCard label="OLT 设备" :value="data.device?.total || 0" hint="当前权限范围" />
        <MetricCard label="采集成功率" :value="`${data.collect?.success_rate || 0}%`" :hint="`${data.collect?.success_count || 0} 台成功`" tone="green" />
        <MetricCard label="质差 ONU" :value="data.quality?.current_bad || 0" hint="当前最新记录" tone="orange" />
        <MetricCard label="性能告警" :value="performanceAlarm" :hint="`CPU ${data.perf?.cpu_alarm || 0} / 内存 ${data.perf?.mem_alarm || 0}`" tone="red" />
      </view>

      <view class="section-card">
        <view class="section-head">
          <view class="section-head-title">近 7 日质差趋势</view>
          <view class="section-head-meta">每日最新采样</view>
        </view>
        <view v-if="trend.length" class="trend-area">
          <view v-for="point in trend" :key="point.stat_date" class="trend-column">
            <view class="trend-value">{{ point.bad_count || 0 }}</view>
            <view class="trend-track"><view class="trend-bar" :style="{ height: `${barHeight(point.bad_count)}%` }" /></view>
            <view class="trend-date">{{ shortDate(point.stat_date) }}</view>
          </view>
        </view>
        <EmptyState v-else mark="趋" title="暂无趋势数据" description="完成采集后会在这里显示近 7 日质差变化。" />
      </view>

      <view class="section-card">
        <view class="section-head">
          <view class="section-head-title">采集状态</view>
          <view class="section-head-meta">{{ collectorTotal }} 台设备</view>
        </view>
        <view class="state-list">
          <view v-for="item in data.collector_state || []" :key="item.status" class="state-row">
            <StatusBadge :value="item.status" />
            <view class="state-line"><view class="state-fill" :class="stateTone(item.status)" :style="{ width: `${statePercent(item.total)}%` }" /></view>
            <view class="state-count">{{ item.total }}</view>
          </view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head">
          <view class="section-head-title">高风险 ONU</view>
          <view class="section-head-meta" @tap="go('/pages/netops/quality/index')">查看全部 ›</view>
        </view>
        <view v-if="riskList.length" class="risk-list">
          <view v-for="item in riskList" :key="`${item.olt_device_id}-${item.onu_mac}`" class="risk-row" @tap="openOnu(item)">
            <view class="risk-main">
              <view class="risk-title">{{ formatMac(item.onu_mac) }}</view>
              <view class="risk-meta">{{ item.olt_name || '--' }} · {{ item.pon_port || '--' }}</view>
              <view class="risk-address">{{ item.room_group || item.region || '--' }} / {{ item.room || '--' }}</view>
            </view>
            <view class="risk-side">
              <view class="power-value">{{ displayPower(item.rx_power) }}</view>
              <StatusBadge :value="item.quality_code || 'warning'" :text="qualityText(item.quality_code)" />
            </view>
          </view>
        </view>
        <EmptyState v-else mark="安" title="当前没有高风险 ONU" description="最新采集结果未发现需要优先关注的光功率异常。" />
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import MetricCard from '../../../components/netops/MetricCard.vue'
import StatusBadge from '../../../components/netops/StatusBadge.vue'
import { getNetopsDashboard } from '../../../api/netops'
import { messageLabel } from '../../../utils/labels'

const loading = ref(true)
const data = ref({})

const quickActions = [
  { name: 'ONU 查询', icon: '光', tone: 'blue', path: '/pages/netops/onu/index' },
  { name: '质差管理', icon: '质', tone: 'orange', path: '/pages/netops/quality/index' },
  { name: 'OLT 性能', icon: '性', tone: 'purple', path: '/pages/netops/performance/index' },
  { name: '采集监控', icon: '采', tone: 'green', path: '/pages/netops/collector/index' }
]

const trend = computed(() => data.value.quality_trend || [])
const riskList = computed(() => data.value.risk_list || [])
const performanceAlarm = computed(() => Number(data.value.perf?.cpu_alarm || 0) + Number(data.value.perf?.mem_alarm || 0))
const collectorTotal = computed(() => (data.value.collector_state || []).reduce((sum, item) => sum + Number(item.total || 0), 0))
const latestText = computed(() => data.value.collect?.latest_finished_at ? `最近采集 ${data.value.collect.latest_finished_at}` : '汇总 FTTH / HFC 网络运行状态')
const maxTrend = computed(() => Math.max(...trend.value.map((item) => Number(item.bad_count || 0)), 1))

onLoad(loadData)
onPullDownRefresh(() => loadData(true))

function loadData(fromPull = false) {
  loading.value = true
  getNetopsDashboard()
    .then((result) => { data.value = result || {} })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => {
      loading.value = false
      if (fromPull) uni.stopPullDownRefresh()
    })
}

function go(path) { uni.navigateTo({ url: path }) }
function barHeight(value) { return Math.max(8, Math.round(Number(value || 0) / maxTrend.value * 100)) }
function shortDate(value) { return String(value || '').slice(5) || '--' }
function statePercent(value) { return collectorTotal.value ? Math.max(5, Number(value || 0) / collectorTotal.value * 100) : 0 }
function stateTone(status) { return String(status).includes('success') ? 'ok' : String(status).includes('running') ? 'info' : 'danger' }
function displayPower(value) { return value === null || value === undefined ? '-- dBm' : `${value} dBm` }
function formatMac(value) { return String(value || '').replace(/(.{2})(?=.)/g, '$1:').toUpperCase() || '--' }
function qualityText(code) { return ({ rx_low: '光功率过低', rx_high: '光功率过高', rx_missing: '光功率缺失' })[code] || '质差' }
function openOnu(item) { go(`/pages/netops/onu/index?keyword=${encodeURIComponent(item.onu_mac || '')}&type=mac`) }
</script>

<style scoped>
.dashboard-page { padding-top: 0; }
.hero { display:flex; align-items:center; justify-content:space-between; gap:20rpx; margin:0 -24rpx 22rpx; padding:42rpx 30rpx 38rpx; border-radius:0 0 30rpx 30rpx; background:linear-gradient(145deg,#203147,#315478); color:#fff; }
.eyebrow { color:rgba(255,255,255,.55); font-size:18rpx; letter-spacing:3rpx; }
.hero-title { margin-top:8rpx; font-size:38rpx; font-weight:750; }
.hero-sub { margin-top:10rpx; color:rgba(255,255,255,.68); font-size:22rpx; }
.refresh { padding:12rpx 18rpx; border:1rpx solid rgba(255,255,255,.25); border-radius:99rpx; color:rgba(255,255,255,.88); font-size:22rpx; }
.quick-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12rpx; margin-bottom:20rpx; padding:18rpx 10rpx; border:1rpx solid #e3e9f0; border-radius:18rpx; background:#fff; }
.quick-item { display:flex; flex-direction:column; align-items:center; padding:8rpx 0; }
.quick-icon { display:flex; align-items:center; justify-content:center; width:64rpx; height:64rpx; border-radius:17rpx; background:#eaf2fd; color:#2765ac; font-size:25rpx; font-weight:700; }
.quick-icon.orange { background:#fff0df; color:#b36b18; }
.quick-icon.purple { background:#f0ecff; color:#6851be; }
.quick-icon.green { background:#e4f5ef; color:#137759; }
.quick-name { margin-top:10rpx; color:#39485b; font-size:21rpx; }
.metric-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16rpx; margin-bottom:20rpx; }
.trend-area { display:flex; align-items:flex-end; height:250rpx; padding:28rpx 18rpx 22rpx; }
.trend-column { display:flex; flex:1; min-width:0; flex-direction:column; align-items:center; height:100%; }
.trend-value { color:#667385; font-size:19rpx; }
.trend-track { display:flex; flex:1; align-items:flex-end; width:28rpx; margin:10rpx 0; border-radius:8rpx; background:#edf2f7; overflow:hidden; }
.trend-bar { width:100%; border-radius:8rpx 8rpx 0 0; background:linear-gradient(#4c8ad4,#2a68b0); }
.trend-date { color:#8a96a5; font-size:18rpx; }
.state-list { padding:8rpx 24rpx 20rpx; }
.state-row { display:flex; align-items:center; gap:16rpx; min-height:68rpx; }
.state-line { flex:1; height:10rpx; overflow:hidden; border-radius:99rpx; background:#edf1f5; }
.state-fill { height:100%; background:#d0544e; }.state-fill.ok{background:#17906d}.state-fill.info{background:#3d7cc5}
.state-count { width:54rpx; color:#526174; font-size:23rpx; text-align:right; }
.risk-list { padding:0 24rpx; }
.risk-row { display:flex; align-items:center; justify-content:space-between; gap:20rpx; padding:24rpx 0; border-bottom:1rpx solid #edf1f5; }
.risk-row:last-child { border-bottom:0; }.risk-main{min-width:0;flex:1}.risk-title{color:#172133;font-family:monospace;font-size:27rpx;font-weight:700}.risk-meta{margin-top:8rpx;color:#536277;font-size:23rpx}.risk-address{margin-top:5rpx;color:#8a95a3;font-size:21rpx}.risk-side{text-align:right}.power-value{margin-bottom:9rpx;color:#bd433d;font-size:27rpx;font-weight:700}
</style>
