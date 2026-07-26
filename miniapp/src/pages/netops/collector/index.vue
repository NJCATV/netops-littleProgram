<template>
  <view class="netops-page">
    <view class="tab-bar">
      <view v-for="tab in tabs" :key="tab.value" class="tab" :class="{ active: currentTab === tab.value }" @tap="switchTab(tab.value)">{{ tab.label }}</view>
    </view>

    <view v-if="currentTab !== 'tasks'" class="search-bar filter-search">
      <input v-model="keyword" class="search-input" placeholder="搜索设备名称或 IP" confirm-type="search" @confirm="reload" />
      <button class="search-button" @tap="reload">查询</button>
    </view>

    <view v-if="currentTab === 'overview'" class="section-card">
      <view class="section-head"><view class="section-head-title">设备采集状态</view><view class="section-head-meta">{{ items.length }} 台</view></view>
      <view v-if="items.length" class="collector-list">
        <view v-for="item in items" :key="item.olt_device_id" class="collector-item">
          <view class="collector-top"><view><view class="collector-name">{{ item.name || item.region || `OLT ${item.olt_device_id}` }}</view><view class="collector-id">ID {{ item.olt_device_id }} · {{ item.primary_ip || item.region || '--' }}</view></view><StatusBadge :value="item.last_result_status" /></view>
          <view class="collector-stats">
            <view><text>Ping</text><strong :class="flagClass(item.last_is_ping)">{{ flag(item.last_is_ping) }}</strong></view>
            <view><text>SNMP</text><strong :class="flagClass(item.last_is_snmp)">{{ flag(item.last_is_snmp) }}</strong></view>
            <view><text>MAC</text><strong>{{ item.last_mac_cnt ?? '--' }}</strong></view>
            <view><text>光功率</text><strong>{{ item.last_power_cnt ?? '--' }}</strong></view>
            <view><text>耗时</text><strong>{{ item.last_total_cost_ms ? `${item.last_total_cost_ms}ms` : '--' }}</strong></view>
          </view>
          <view v-if="item.last_fail_reason" class="fail-reason">{{ item.last_fail_reason }}</view>
          <view class="collector-time">{{ item.last_finished_at || '暂无完成时间' }}</view>
        </view>
      </view>
      <view v-else-if="loading" class="status-text">正在加载采集状态...</view>
      <EmptyState v-else mark="采" title="暂无采集状态" />
    </view>

    <view v-else-if="currentTab === 'tasks'" class="section-card">
      <view class="section-head"><view class="section-head-title">采集任务</view><view class="section-head-meta">{{ total }} 项</view></view>
      <view v-if="items.length" class="task-list">
        <view v-for="item in items" :key="item.task_key" class="task-item">
          <view class="collector-top"><view><view class="collector-name">{{ item.task_name || item.task_key }}</view><view class="collector-id">{{ item.task_type || '--' }}</view></view><StatusBadge :value="item.status" /></view>
          <view class="task-line"><text>最近开始</text><text>{{ item.last_started_at || item.started_at || '--' }}</text></view>
          <view class="task-line"><text>最近完成</text><text>{{ item.last_finished_at || item.finished_at || '--' }}</text></view>
          <view v-if="item.fail_reason || item.last_error" class="fail-reason">{{ item.fail_reason || item.last_error }}</view>
        </view>
      </view>
      <view v-else-if="loading" class="status-text">正在加载任务...</view>
      <EmptyState v-else mark="任" title="暂无采集任务" />
    </view>

    <view v-else class="section-card">
      <view class="section-head"><view class="section-head-title">采集历史</view><view class="section-head-meta">{{ total }} 条</view></view>
      <view v-if="items.length" class="history-list">
        <view v-for="item in items" :key="item.round_id" class="history-item">
          <view class="collector-top"><view><view class="collector-name">{{ item.name || `OLT ${item.olt_device_id}` }}</view><view class="collector-id">{{ item.region || '--' }} / {{ item.room || '--' }}</view></view><StatusBadge :value="historyStatus(item)" /></view>
          <view class="history-data">MAC {{ item.mac_cnt ?? '--' }} · 光功率 {{ item.power_cnt ?? '--' }} · {{ item.total_cost_ms || 0 }}ms</view>
          <view v-if="item.fail_reason" class="fail-reason">{{ item.fail_reason }}</view>
          <view class="collector-time">{{ item.finished_at || '--' }}</view>
        </view>
      </view>
      <view v-else-if="loading" class="status-text">正在加载采集历史...</view>
      <EmptyState v-else mark="史" title="暂无采集历史" />
      <view v-if="items.length < total" class="load-more" @tap="loadMore">继续加载</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onReachBottom } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import StatusBadge from '../../../components/netops/StatusBadge.vue'
import { getCollectorDevices, getCollectorHistory, getCollectorOverview, getCollectorTasks } from '../../../api/netops'
import { messageLabel } from '../../../utils/labels'

const tabs = [{ value: 'overview', label: '设备状态' }, { value: 'tasks', label: '任务进度' }, { value: 'history', label: '采集历史' }]
const currentTab = ref('overview')
const keyword = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

onLoad(reload)
onReachBottom(loadMore)

function switchTab(value) { currentTab.value = value; keyword.value = ''; reload() }
function reload() { page.value = 1; items.value = []; loadData() }
function loadMore() { if (currentTab.value === 'history' && !loading.value && items.value.length < total.value) { page.value += 1; loadData(true) } }
function loadData(append = false) {
  loading.value = true
  let action
  if (currentTab.value === 'overview') action = keyword.value ? getCollectorDevices({ keyword: keyword.value, page: 1, size: 80 }) : getCollectorOverview()
  else if (currentTab.value === 'tasks') action = getCollectorTasks({ page: 1, size: 80 })
  else action = getCollectorHistory({ keyword: keyword.value, page: page.value, size: 30 })
  action.then((data) => {
    const rows = Array.isArray(data) ? data : (data.items || [])
    items.value = append ? items.value.concat(rows) : rows
    total.value = Number(Array.isArray(data) ? rows.length : (data.total || rows.length))
  }).catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' })).finally(() => { loading.value = false })
}
function flag(value) { return Number(value) === 1 ? '正常' : '失败' }
function flagClass(value) { return Number(value) === 1 ? 'ok-text' : 'danger-text' }
function historyStatus(item) { return Number(item.is_ping) === 1 && Number(item.is_snmp) === 1 && !item.fail_reason ? 'success' : 'failed' }
</script>

<style scoped>
.tab-bar{display:flex;margin-bottom:16rpx;padding:7rpx;border-radius:14rpx;background:#e7edf3}.tab{flex:1;padding:16rpx 8rpx;border-radius:10rpx;color:#68778a;font-size:23rpx;text-align:center}.tab.active{background:#fff;color:#255f9e;font-weight:700}.filter-search{margin-bottom:18rpx}.collector-list,.task-list,.history-list{padding:0 24rpx}.collector-item,.task-item,.history-item{padding:24rpx 0;border-bottom:1rpx solid #edf1f5}.collector-item:last-child,.task-item:last-child,.history-item:last-child{border-bottom:0}.collector-top{display:flex;align-items:center;justify-content:space-between;gap:18rpx}.collector-name{color:#25364b;font-size:26rpx;font-weight:700}.collector-id{margin-top:6rpx;color:#8894a3;font-size:20rpx}.collector-stats{display:grid;grid-template-columns:repeat(5,1fr);margin-top:18rpx;padding:16rpx 6rpx;border-radius:12rpx;background:#f5f8fa}.collector-stats view{text-align:center}.collector-stats text{display:block;color:#8894a3;font-size:17rpx}.collector-stats strong{display:block;margin-top:5rpx;color:#3c4c60;font-size:19rpx}.collector-stats .ok-text{color:#17795c}.collector-stats .danger-text{color:#c14b45}.fail-reason{margin-top:14rpx;padding:12rpx 15rpx;border-radius:9rpx;background:#fff0ef;color:#a54843;font-size:20rpx;line-height:1.45}.collector-time{margin-top:12rpx;color:#98a1ad;font-size:19rpx}.task-line{display:flex;justify-content:space-between;gap:18rpx;margin-top:13rpx;color:#748193;font-size:20rpx}.task-line text:last-child{text-align:right}.history-data{margin-top:14rpx;color:#59697d;font-size:21rpx}
</style>
