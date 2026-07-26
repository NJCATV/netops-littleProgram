<template>
  <view class="netops-page">
    <view class="olt-picker-row">
      <view class="olt-picker" @tap="oltPickerVisible=true">{{ selectedOltLabel }}⌄</view>
      <text>优先按 OLT 定位，再补充关键词</text>
    </view>
    <view class="search-bar">
      <input v-model="keyword" class="search-input" placeholder="搜索 OLT、机房、型号或 IP" confirm-type="search" @confirm="reload" />
      <button class="search-button" @tap="reload">查询</button>
    </view>
    <view class="condition-row">
      <view v-for="item in conditions" :key="item.key" class="condition" :class="{ active: selected[item.key] }" @tap="toggle(item.key)">{{ item.label }}</view>
    </view>

    <view class="stats-strip">
      <view><strong>{{ stats.abnormal || 0 }}</strong><text>异常设备</text></view>
      <view><strong>{{ stats.cpu_alarm || 0 }}</strong><text>CPU 告警</text></view>
      <view><strong>{{ stats.mem_alarm || 0 }}</strong><text>内存告警</text></view>
      <view><strong>{{ stats.collect_failure_count || 0 }}</strong><text>采集异常</text></view>
    </view>

    <view class="section-card">
      <view class="section-head"><view class="section-head-title">OLT 性能</view><view class="section-head-meta">{{ total }} 台</view></view>
      <view v-if="items.length" class="device-list">
        <view v-for="item in items" :key="item.olt_device_id" class="device-card" @tap="openDetail(item)">
          <view class="device-top">
            <view class="device-copy"><view class="device-name">{{ item.name || `OLT ${item.olt_device_id}` }}</view><view class="device-meta">{{ item.room_group || item.region || '--' }} / {{ item.room || '--' }}</view></view>
            <StatusBadge :value="item.status" :text="item.status_label || item.status" />
          </view>
          <view class="usage-grid">
            <view class="usage"><view class="usage-head"><text>CPU</text><strong>{{ percent(item.cpu_usage) }}</strong></view><view class="usage-track"><view class="usage-fill cpu" :class="usageTone(item.cpu_usage)" :style="{ width: percent(item.cpu_usage) }" /></view></view>
            <view class="usage"><view class="usage-head"><text>内存</text><strong>{{ percent(item.mem_usage) }}</strong></view><view class="usage-track"><view class="usage-fill mem" :class="usageTone(item.mem_usage)" :style="{ width: percent(item.mem_usage) }" /></view></view>
          </view>
          <view v-if="item.board_count" class="board-line">板卡 {{ item.board_count }} 块 · 峰值 CPU {{ percent(item.board_cpu_max) }} · 内存 {{ percent(item.board_mem_max) }}</view>
          <view class="device-foot"><text>{{ item.device_model || '--' }}</text><text>{{ item.latest_time || '未采集' }} ›</text></view>
        </view>
      </view>
      <view v-else-if="loading" class="status-text">正在加载性能状态...</view>
      <EmptyState v-else mark="性" title="没有匹配的 OLT" description="可切换异常条件或修改搜索关键字。" />
      <view v-if="items.length < total" class="load-more" @tap="loadMore">{{ loading ? '加载中...' : '继续加载' }}</view>
    </view>

    <view v-if="detailVisible" class="overlay" @tap="closeDetail">
      <view class="detail-sheet" @tap.stop>
        <view class="sheet-handle" />
        <view class="sheet-head"><view><view class="sheet-title">{{ detail.device?.name || 'OLT 性能详情' }}</view><view class="sheet-sub">{{ detail.device?.primary_ip || '--' }} · {{ detail.device?.device_model || '--' }}</view></view><view class="sheet-close" @tap="closeDetail">×</view></view>
        <scroll-view scroll-y class="sheet-scroll">
          <view class="detail-kpis">
            <view><text>设备 CPU</text><strong>{{ percent(detail.device?.cpu_usage) }}</strong></view>
            <view><text>设备内存</text><strong>{{ percent(detail.device?.mem_usage) }}</strong></view>
            <view><text>板卡数量</text><strong>{{ detail.boards?.length || 0 }}</strong></view>
          </view>
          <view class="detail-title">板卡性能</view>
          <view v-for="board in detail.boards || []" :key="board.slot_id" class="board-row"><view><strong>槽位 {{ board.slot_id }}</strong><text>{{ board.board_name || '板卡' }}</text></view><view><StatusBadge :value="board.status" /><text>CPU {{ percent(board.cpu_usage) }} / 内存 {{ percent(board.mem_usage) }}</text></view></view>
          <EmptyState v-if="!detail.boards?.length" mark="板" title="暂无板卡性能" />
          <view class="detail-title">端口状态</view>
          <view v-for="port in (detail.ports || []).slice(0, 30)" :key="port.if_index" class="port-row"><text>{{ port.port_category || '端口' }} {{ port.if_index }}</text><StatusBadge :value="String(port.if_oper_status)" :text="String(port.if_oper_status) === '1' ? '在线' : '离线'" /></view>
        </scroll-view>
      </view>
    </view>
    <view v-if="oltPickerVisible" class="olt-mask" @tap="oltPickerVisible=false"><view class="olt-sheet" @tap.stop><view class="olt-sheet-head"><text>按区域、机房选择 OLT</text><text @tap="oltPickerVisible=false">取消</text></view><view class="olt-columns"><scroll-view scroll-y class="olt-column"><view v-for="item in regions" :key="item" :class="{active:selectedRegion===item}" @tap="chooseRegion(item)">{{ regionLabel(item) }}</view></scroll-view><scroll-view scroll-y class="olt-column"><view v-for="item in rooms" :key="item" :class="{active:selectedRoom===item}" @tap="selectedRoom=item">{{ item }}</view></scroll-view><scroll-view scroll-y class="olt-column"><view :class="{active:!selectedOltId}" @tap="selectOlt(null)">全部 OLT</view><view v-for="item in filteredOlts" :key="item.olt_device_id" :class="{active:String(selectedOltId)===String(item.olt_device_id)}" @tap="selectOlt(item)">{{ item.name }}</view></scroll-view></view></view></view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad, onReachBottom } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import StatusBadge from '../../../components/netops/StatusBadge.vue'
import { getOltDeviceOptions, getOltPerformance, getOltPerformanceDetail } from '../../../api/netops'
import { messageLabel } from '../../../utils/labels'

const conditions = [{ key: 'cpu', label: 'CPU 异常' }, { key: 'mem', label: '内存异常' }, { key: 'collect_failure', label: '采集异常' }]
// 默认只看 CPU / 内存性能告警；采集异常由用户主动勾选。
const selected = reactive({ cpu: true, mem: true, collect_failure: false })
const keyword = ref('')
const selectedOltId = ref('')
const oltOptions = ref([])
const oltPickerVisible = ref(false)
const selectedRegion = ref('全部区域')
const selectedRoom = ref('全部机房')
const regionLabels = { chengbei:'城北',chengdong:'城东',chengnan:'城南',chengxi:'城西',gaochun:'高淳',jiangning:'江宁',lishui:'溧水',liuhe:'六合',pukou:'浦口',qixia:'栖霞' }
const selectedOltLabel = computed(() => selectedOltId.value ? ((oltOptions.value.find((item) => String(item.olt_device_id) === String(selectedOltId.value)) || {}).name || '已选 OLT') : '全部 OLT')
const regions = computed(() => ['全部区域'].concat([...new Set(oltOptions.value.map(item=>item.region).filter(Boolean))]))
const rooms = computed(() => ['全部机房'].concat([...new Set(oltOptions.value.filter(item=>selectedRegion.value==='全部区域'||item.region===selectedRegion.value).map(item=>item.room||item.room_group).filter(Boolean))]))
const filteredOlts = computed(() => oltOptions.value.filter(item=>(selectedRegion.value==='全部区域'||item.region===selectedRegion.value)&&(selectedRoom.value==='全部机房'||(item.room||item.room_group)===selectedRoom.value)))
const items = ref([])
const stats = ref({})
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const detailVisible = ref(false)
const detail = ref({})

onLoad(() => { loadOltOptions(); reload() })
onReachBottom(loadMore)

function toggle(key) { selected[key] = !selected[key]; reload() }
function reload() { page.value = 1; items.value = []; loadData() }
function loadMore() { if (!loading.value && items.value.length < total.value) { page.value += 1; loadData(true) } }
function loadData(append = false) {
  loading.value = true
  getOltPerformance({ page: page.value, size: 20, keyword: keyword.value.trim(), olt_device_ids: selectedOltId.value, condition_cpu: selected.cpu ? 1 : 0, condition_mem: selected.mem ? 1 : 0, condition_collect_failure: selected.collect_failure ? 1 : 0 })
    .then((data) => { items.value = append ? items.value.concat(data.items || []) : (data.items || []); total.value = Number(data.total || 0); stats.value = data.stats || {} })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => { loading.value = false })
}
function loadOltOptions() { getOltDeviceOptions().then((data) => { oltOptions.value = data.items || [] }).catch(() => {}) }
function chooseRegion(value){selectedRegion.value=value;selectedRoom.value='全部机房'}
function selectOlt(item){selectedOltId.value=item?String(item.olt_device_id):'';oltPickerVisible.value=false;reload()}
function regionLabel(value){return regionLabels[value]||value}
function openDetail(item) {
  uni.showLoading({ title: '加载详情' })
  getOltPerformanceDetail({ olt_device_id: item.olt_device_id })
    .then((data) => { detail.value = data; detailVisible.value = true })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => uni.hideLoading())
}
function closeDetail() { detailVisible.value = false }
function percent(value) { const number = Number(value); return Number.isFinite(number) ? `${Math.max(0, Math.min(100, number)).toFixed(1)}%` : '--' }
function usageTone(value) { const number = Number(value); return number >= 90 ? 'critical' : number >= 80 ? 'warning' : '' }
</script>

<style scoped>
.olt-picker-row{display:flex;align-items:center;justify-content:space-between;gap:14rpx;margin-bottom:12rpx}.olt-picker{max-width:370rpx;padding:13rpx 18rpx;overflow:hidden;border:1rpx solid #cfe0f2;border-radius:12rpx;background:#f3f8ff;color:#2864a7;font-size:22rpx;text-overflow:ellipsis;white-space:nowrap}.olt-picker-row>text{color:#8996a5;font-size:19rpx}.olt-mask{position:fixed;z-index:50;inset:0;display:flex;align-items:flex-end;background:rgba(15,25,38,.42)}.olt-sheet{width:100%;border-radius:24rpx 24rpx 0 0;background:#fff}.olt-sheet-head{display:flex;justify-content:space-between;padding:26rpx 28rpx;border-bottom:1rpx solid #e8edf2;color:#2864a7;font-size:25rpx}.olt-sheet-head text:first-child{color:#28394e;font-size:29rpx;font-weight:700}.olt-columns{display:grid;grid-template-columns:repeat(3,1fr);height:54vh}.olt-column{border-right:1rpx solid #edf1f5}.olt-column:last-child{border:0}.olt-column view{padding:22rpx 16rpx;color:#65758a;font-size:22rpx;line-height:1.35}.olt-column view.active{background:#edf5ff;color:#2864a7;font-weight:700}.condition-row{display:flex;gap:10rpx;margin:14rpx 0 18rpx}.condition{padding:12rpx 17rpx;border:1rpx solid #dce4ec;border-radius:99rpx;background:#fff;color:#718094;font-size:21rpx}.condition.active{border-color:#87acd6;background:#eaf3ff;color:#2864a7}.stats-strip{display:grid;grid-template-columns:repeat(4,1fr);margin-bottom:20rpx;padding:20rpx 8rpx;border:1rpx solid #e3e9f0;border-radius:17rpx;background:#fff}.stats-strip view{text-align:center}.stats-strip strong{display:block;color:#27384d;font-size:29rpx}.stats-strip text{display:block;margin-top:5rpx;color:#8692a1;font-size:18rpx}.device-list{padding:0 24rpx}.device-card{padding:25rpx 0;border-bottom:1rpx solid #edf1f5}.device-card:last-child{border-bottom:0}.device-top,.device-foot{display:flex;align-items:center;justify-content:space-between;gap:16rpx}.device-copy{min-width:0}.device-name{overflow:hidden;color:#203045;font-size:27rpx;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.device-meta{margin-top:6rpx;color:#8390a0;font-size:20rpx}.usage-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:22rpx;margin-top:22rpx}.usage-head{display:flex;justify-content:space-between;color:#69778a;font-size:20rpx}.usage-head strong{color:#33445a}.usage-track{height:10rpx;margin-top:9rpx;overflow:hidden;border-radius:99rpx;background:#edf1f5}.usage-fill{height:100%;border-radius:99rpx;background:#2c75c6}.usage-fill.mem{background:#6e5bc8}.usage-fill.warning{background:#d38a2a}.usage-fill.critical{background:#d15049}.board-line{margin-top:15rpx;padding:12rpx 14rpx;border-radius:9rpx;background:#f6f8fa;color:#6f7c8d;font-size:19rpx}.device-foot{margin-top:16rpx;color:#8c97a5;font-size:19rpx}.overlay{position:fixed;z-index:20;inset:0;display:flex;align-items:flex-end;background:rgba(18,28,40,.46)}.detail-sheet{width:100%;height:78vh;border-radius:28rpx 28rpx 0 0;background:#f4f7fa}.sheet-handle{width:70rpx;height:8rpx;margin:14rpx auto;border-radius:99rpx;background:#c6ced8}.sheet-head{display:flex;align-items:center;justify-content:space-between;padding:12rpx 28rpx 24rpx}.sheet-title{font-size:31rpx;font-weight:750}.sheet-sub{margin-top:6rpx;color:#7d8998;font-size:21rpx}.sheet-close{padding:8rpx;color:#7a8797;font-size:44rpx}.sheet-scroll{height:calc(78vh - 120rpx);padding:0 24rpx;box-sizing:border-box}.detail-kpis{display:grid;grid-template-columns:repeat(3,1fr);padding:22rpx 10rpx;border-radius:16rpx;background:#fff}.detail-kpis view{text-align:center}.detail-kpis text{display:block;color:#8491a0;font-size:20rpx}.detail-kpis strong{display:block;margin-top:7rpx;color:#24354a;font-size:28rpx}.detail-title{margin:26rpx 0 12rpx;color:#314157;font-size:24rpx;font-weight:700}.board-row,.port-row{display:flex;align-items:center;justify-content:space-between;gap:18rpx;padding:20rpx;border-bottom:1rpx solid #edf1f5;background:#fff}.board-row:first-of-type,.port-row:first-of-type{border-radius:14rpx 14rpx 0 0}.board-row strong,.board-row text{display:block}.board-row strong{font-size:23rpx}.board-row text{margin-top:5rpx;color:#8390a0;font-size:19rpx}.board-row>view:last-child{text-align:right}.port-row{font-size:22rpx}
</style>
