<template>
  <view class="netops-page onu-page">
    <view class="mode-tabs">
      <view v-for="mode in modes" :key="mode.value" class="mode-tab" :class="{ active: searchType === mode.value }" @tap="searchType = mode.value">{{ mode.label }}</view>
    </view>
    <view class="search-bar">
      <input v-model="keyword" class="search-input" :placeholder="placeholder" confirm-type="search" @confirm="runSearch" />
      <button class="search-button" :loading="loading" @tap="runSearch">查询</button>
    </view>

    <view v-if="loading" class="section-card result-space"><view class="status-text">正在查询 ONU 与用户资料...</view></view>
    <EmptyState v-else-if="searched && !primary" mark="查" title="没有找到匹配的 ONU" description="请检查 MAC、GDF 账号或尝试使用姓名、地址搜索。" />
    <EmptyState v-else-if="!primary" mark="光" title="查询单台 ONU" description="支持 MAC、GDF 账号、用户姓名和装机地址，系统会优先展示最可信记录。" />

    <template v-else>
      <view class="primary-card">
        <view class="primary-head">
          <view>
            <view class="primary-label">当前主记录</view>
            <view class="mac">{{ primary.display_mac || formatMac(primary.onu_mac) }}</view>
          </view>
          <StatusBadge :value="primary.quality_bad ? 'warning' : 'normal'" :text="primary.quality_bad ? (primary.quality_label || '质差') : '光功率正常'" />
        </view>
        <view class="power-panel">
          <view class="power-item">
            <view class="power-label">接收光功率 RX</view>
            <view class="power-value" :class="{ bad: primary.quality_bad }">{{ power(primary.rx_power) }}</view>
          </view>
          <view class="power-divider" />
          <view class="power-item">
            <view class="power-label">发送光功率 TX</view>
            <view class="power-value">{{ power(primary.tx_power) }}</view>
          </view>
        </view>
        <view class="info-grid">
          <view class="info-cell"><view class="info-label">OLT</view><view class="info-value">{{ primary.olt_name || '--' }}</view><view class="info-sub">{{ primary.device_model || '--' }} · {{ primary.primary_ip || '--' }}</view></view>
          <view class="info-cell"><view class="info-label">PON 端口</view><view class="info-value">{{ primary.uplink_port_norm || primary.pon_port || '--' }}</view><view class="info-sub">ifIndex {{ primary.if_index || '--' }}</view></view>
          <view class="info-cell"><view class="info-label">BOSS 用户</view><view class="info-value">{{ primary.boss_customer_name || '--' }}</view><view class="info-sub">{{ primary.gdf_account || '无 GDF 账号' }}</view></view>
          <view class="info-cell"><view class="info-label">最近采集</view><view class="info-value small">{{ primary.query_time || '--' }}</view></view>
        </view>
        <view v-if="primary.boss_address" class="address-row"><text class="address-label">装机地址</text><text class="address-value">{{ primary.boss_address }}</text></view>
        <button class="realtime-button" :loading="realtimeLoading" @tap="loadRealtime">实时采集光功率</button>
      </view>

      <view v-if="realtime" class="section-card realtime-card">
        <view class="section-head"><view class="section-head-title">实时采集结果</view><view class="section-head-meta">{{ realtime.query_time || '刚刚' }}</view></view>
        <view class="realtime-values">
          <view><text>RX</text><strong>{{ power(realtime.rx_power) }}</strong></view>
          <view><text>TX</text><strong>{{ power(realtime.tx_power) }}</strong></view>
          <view><text>来源</text><strong>{{ realtime.source || '--' }}</strong></view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head"><view class="section-head-title">近 7 日光功率</view><view class="section-head-meta">{{ history.length }} 个采样点</view></view>
        <view v-if="history.length" class="history-wrap">
          <view class="history-summary"><text>最低 {{ historyMin }} dBm</text><text>最高 {{ historyMax }} dBm</text></view>
          <scroll-view scroll-x class="history-scroll">
            <view class="history-chart" :style="{ width: `${Math.max(620, sampledHistory.length * 64)}rpx` }">
              <view v-for="(point, index) in sampledHistory" :key="`${point.sample_time}-${index}`" class="history-point">
                <view class="point-value">{{ point.rx_power }}</view>
                <view class="point-track"><view class="point-dot" :class="{ bad: point.quality_bad }" :style="{ bottom: `${pointPosition(point.rx_power)}%` }" /></view>
                <view class="point-time"><text>{{ shortDate(point.sample_time) }}</text><text>{{ shortTime(point.sample_time) }}</text></view>
              </view>
            </view>
          </scroll-view>
        </view>
        <EmptyState v-else mark="史" title="暂无历史采样" description="当前 ONU 还没有可显示的光功率历史。" />
      </view>

      <view v-if="items.length > 1" class="section-card">
        <view class="section-head"><view class="section-head-title">疑似重复记录</view><view class="section-head-meta">{{ items.length - 1 }} 条</view></view>
        <view class="duplicate-list">
          <view v-for="item in items.slice(1)" :key="`${item.olt_device_id}-${item.if_index}-${item.onu_mac}`" class="duplicate-row" @tap="openDuplicate(item)">
            <view class="duplicate-main"><view class="duplicate-mac">{{ item.display_mac || formatMac(item.onu_mac) }}</view><view class="duplicate-meta">{{ item.olt_name || '--' }} · {{ item.pon_port || '--' }}</view></view>
            <view class="duplicate-power"><view>{{ power(item.rx_power) }}</view><StatusBadge :value="item.quality_bad ? 'warning' : 'normal'" :text="item.quality_bad ? '质差' : '正常'" /><view class="duplicate-link">查看详情 ›</view></view>
          </view>
        </view>
      </view>
    </template>

    <view v-if="selectedDuplicate" class="overlay" @tap="selectedDuplicate = null">
      <view class="duplicate-sheet" @tap.stop>
        <view class="sheet-head"><view><view class="sheet-kicker">疑似重复记录详情</view><view class="sheet-mac">{{ selectedDuplicate.display_mac || formatMac(selectedDuplicate.onu_mac) }}</view></view><view class="sheet-close" @tap="selectedDuplicate = null">×</view></view>
        <view class="duplicate-detail-grid">
          <view><text>OLT</text><strong>{{ selectedDuplicate.olt_name || '--' }}</strong></view>
          <view><text>PON 端口</text><strong>{{ selectedDuplicate.uplink_port_norm || selectedDuplicate.pon_port || '--' }}</strong></view>
          <view><text>ifIndex</text><strong>{{ selectedDuplicate.if_index || '--' }}</strong></view>
          <view><text>最近采集</text><strong>{{ selectedDuplicate.query_time || '--' }}</strong></view>
          <view><text>RX</text><strong>{{ power(selectedDuplicate.rx_power) }}</strong></view>
          <view><text>TX</text><strong>{{ power(selectedDuplicate.tx_power) }}</strong></view>
        </view>
        <view v-if="selectedDuplicate.boss_address" class="duplicate-address">{{ selectedDuplicate.boss_address }}</view>
        <button class="realtime-button" @tap="useDuplicate">切换到此记录并查看 7 日历史</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import StatusBadge from '../../../components/netops/StatusBadge.vue'
import { getOnuHistory, getRealtimePower, searchOnu } from '../../../api/netops'
import { messageLabel } from '../../../utils/labels'

const modes = [
  { value: 'auto', label: '综合' }, { value: 'mac', label: 'MAC' }, { value: 'account', label: 'GDF账号' }, { value: 'name', label: '姓名' }, { value: 'address', label: '地址' }
]
const keyword = ref('')
const searchType = ref('auto')
const loading = ref(false)
const searched = ref(false)
const items = ref([])
const primary = ref(null)
const history = ref([])
const realtime = ref(null)
const realtimeLoading = ref(false)
const selectedDuplicate = ref(null)

const placeholder = computed(() => ({ mac: '输入至少 6 位 ONU MAC', account: '输入 GDF 账号', name: '输入用户姓名', address: '输入装机地址' })[searchType.value] || '输入 MAC、账号、姓名或地址')
const numericHistory = computed(() => history.value.map((item) => Number(item.rx_power)).filter(Number.isFinite))
const historyMin = computed(() => numericHistory.value.length ? Math.min(...numericHistory.value).toFixed(2) : '--')
const historyMax = computed(() => numericHistory.value.length ? Math.max(...numericHistory.value).toFixed(2) : '--')
const sampledHistory = computed(() => {
  const rows = history.value
  if (rows.length <= 32) return rows
  const step = Math.ceil(rows.length / 32)
  return rows.filter((_, index) => index % step === 0 || index === rows.length - 1)
})

onLoad((options) => {
  if (options?.keyword) {
    keyword.value = decodeURIComponent(options.keyword)
    searchType.value = options.type || 'auto'
    runSearch()
  }
})

function runSearch() {
  if (!keyword.value.trim()) return uni.showToast({ title: '请输入查询条件', icon: 'none' })
  loading.value = true
  searched.value = true
  realtime.value = null
  history.value = []
  searchOnu({ type: searchType.value, keyword: keyword.value.trim() })
    .then((data) => {
      items.value = data.items || []
      primary.value = data.primary || null
      if (primary.value) loadHistory()
    })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => { loading.value = false })
}

function loadHistory() {
  getOnuHistory({ onu_mac: primary.value.onu_mac, olt_device_id: primary.value.olt_device_id, hours: 168 })
    .then((data) => { history.value = data.items || [] })
    .catch(() => { history.value = [] })
}

function loadRealtime() {
  realtimeLoading.value = true
  getRealtimePower({ onu_mac: primary.value.onu_mac, olt_device_id: primary.value.olt_device_id, if_index: primary.value.if_index })
    .then((data) => { realtime.value = data; uni.showToast({ title: '实时采集完成', icon: 'success' }) })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => { realtimeLoading.value = false })
}

function openDuplicate(item) { selectedDuplicate.value = item }
function useDuplicate() {
  primary.value = selectedDuplicate.value
  selectedDuplicate.value = null
  realtime.value = null
  history.value = []
  loadHistory()
  uni.pageScrollTo({ scrollTop: 0, duration: 250 })
}

function power(value) { return value === null || value === undefined || value === '' ? '-- dBm' : `${value} dBm` }
function formatMac(value) { return String(value || '').replace(/(.{2})(?=.)/g, '$1:').toUpperCase() || '--' }
function shortTime(value) { const text = String(value || ''); return text.length >= 16 ? text.slice(11, 16) : '--' }
function shortDate(value) { const text = String(value || ''); return text.length >= 10 ? text.slice(5, 10) : '--' }
function pointPosition(value) {
  const min = Number(historyMin.value); const max = Number(historyMax.value); const current = Number(value)
  if (!Number.isFinite(current) || max === min) return 50
  return Math.max(6, Math.min(94, (current - min) / (max - min) * 88 + 6))
}
</script>

<style scoped>
.mode-tabs{display:flex;gap:8rpx;margin-bottom:14rpx;padding:7rpx;border-radius:14rpx;background:#e8edf3}.mode-tab{flex:1;padding:15rpx 4rpx;border-radius:10rpx;color:#657285;font-size:22rpx;text-align:center}.mode-tab.active{background:#fff;color:#225f9f;font-weight:700;box-shadow:0 2rpx 8rpx rgba(30,52,78,.08)}
.result-space{margin-top:20rpx}.primary-card{margin-top:20rpx;padding:26rpx;border:1rpx solid #dce5ef;border-radius:20rpx;background:#fff}.primary-head{display:flex;align-items:center;justify-content:space-between;gap:18rpx}.primary-label{color:#7c8897;font-size:21rpx}.mac{margin-top:7rpx;color:#172133;font-family:monospace;font-size:34rpx;font-weight:750}.power-panel{display:flex;align-items:stretch;margin-top:24rpx;padding:24rpx 10rpx;border-radius:16rpx;background:#f3f7fb}.power-item{flex:1;text-align:center}.power-divider{width:1rpx;background:#dce4ed}.power-label{color:#758294;font-size:21rpx}.power-value{margin-top:9rpx;color:#176f57;font-size:30rpx;font-weight:750}.power-value.bad{color:#c24c45}.info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rpx;margin-top:22rpx;overflow:hidden;border:1rpx solid #e6ebf1;border-radius:14rpx;background:#e6ebf1}.info-cell{min-width:0;padding:20rpx;background:#fff}.info-label{color:#8793a2;font-size:20rpx}.info-value{margin-top:7rpx;overflow:hidden;color:#27364a;font-size:25rpx;font-weight:650;text-overflow:ellipsis;white-space:nowrap}.info-value.small{font-size:21rpx}.info-sub{margin-top:5rpx;overflow:hidden;color:#8994a2;font-size:19rpx;text-overflow:ellipsis;white-space:nowrap}.address-row{display:flex;gap:18rpx;margin-top:22rpx;padding:18rpx 20rpx;border-radius:12rpx;background:#f8fafc}.address-label{flex:none;color:#788596;font-size:21rpx}.address-value{color:#344459;font-size:22rpx;line-height:1.5}.realtime-button{display:flex;align-items:center;justify-content:center;height:78rpx;margin-top:22rpx;border-radius:13rpx;background:#2269c8;color:#fff;font-size:25rpx;font-weight:650}.realtime-card{margin-top:20rpx}.realtime-values{display:grid;grid-template-columns:repeat(3,1fr);padding:22rpx}.realtime-values view{text-align:center}.realtime-values text{display:block;color:#8793a2;font-size:20rpx}.realtime-values strong{display:block;margin-top:8rpx;color:#223247;font-size:24rpx}.history-wrap{padding:20rpx}.history-summary{display:flex;justify-content:space-between;color:#778496;font-size:20rpx}.history-scroll{width:100%;margin-top:14rpx}.history-chart{display:flex;height:252rpx}.history-point{display:flex;width:64rpx;flex:none;flex-direction:column;align-items:center}.point-value{height:30rpx;color:#6d7b8c;font-size:16rpx;transform:scale(.9)}.point-track{position:relative;flex:1;width:2rpx;background:#e6ebf1}.point-dot{position:absolute;left:-7rpx;width:16rpx;height:16rpx;border:3rpx solid #fff;border-radius:50%;background:#2e73c2;box-shadow:0 0 0 1rpx #2e73c2}.point-dot.bad{background:#cf514a;box-shadow:0 0 0 1rpx #cf514a}.point-time{display:flex;height:48rpx;margin-top:9rpx;flex-direction:column;color:#8a95a3;font-size:16rpx;line-height:1.35;text-align:center}.duplicate-list{padding:0 24rpx}.duplicate-row{display:flex;align-items:center;justify-content:space-between;gap:18rpx;padding:22rpx 0;border-bottom:1rpx solid #edf1f5}.duplicate-row:last-child{border-bottom:0}.duplicate-main{min-width:0}.duplicate-mac{font-family:monospace;color:#28384b;font-size:25rpx;font-weight:700}.duplicate-meta{margin-top:6rpx;color:#7d8998;font-size:21rpx}.duplicate-power{text-align:right;color:#4d5b6d;font-size:22rpx}.duplicate-power .badge{margin-top:7rpx}.duplicate-link{margin-top:8rpx;color:#2b69aa;font-size:18rpx}.overlay{position:fixed;z-index:30;inset:0;display:flex;align-items:flex-end;background:rgba(18,28,40,.48)}.duplicate-sheet{width:100%;padding:28rpx 26rpx 44rpx;border-radius:28rpx 28rpx 0 0;background:#f4f7fa;box-sizing:border-box}.sheet-head{display:flex;align-items:flex-start;justify-content:space-between}.sheet-kicker{color:#7d8997;font-size:21rpx}.sheet-mac{margin-top:7rpx;color:#203047;font-family:monospace;font-size:31rpx;font-weight:750}.sheet-close{padding:0 8rpx;color:#788596;font-size:44rpx}.duplicate-detail-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1rpx;margin-top:22rpx;overflow:hidden;border:1rpx solid #e2e8ef;border-radius:15rpx;background:#e2e8ef}.duplicate-detail-grid view{min-width:0;padding:18rpx;background:#fff}.duplicate-detail-grid text,.duplicate-detail-grid strong{display:block}.duplicate-detail-grid text{color:#8994a2;font-size:19rpx}.duplicate-detail-grid strong{margin-top:6rpx;overflow:hidden;color:#344459;font-size:22rpx;text-overflow:ellipsis;white-space:nowrap}.duplicate-address{margin-top:18rpx;padding:17rpx;border-radius:12rpx;background:#fff;color:#5d6b7d;font-size:21rpx;line-height:1.5}
</style>
