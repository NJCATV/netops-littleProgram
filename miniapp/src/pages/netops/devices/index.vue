<template>
  <view class="netops-page">
    <view class="tab-bar"><view class="tab" :class="{ active: tab === 'list' }" @tap="tab = 'list'">OLT 设备</view><view class="tab" :class="{ active: tab === 'probe' }" @tap="tab = 'probe'">新设备检测</view></view>

    <template v-if="tab === 'list'">
      <view class="search-bar">
        <input v-model="keyword" class="search-input" placeholder="名称、IP、型号、机房" confirm-type="search" @confirm="reload" />
        <button class="search-button" @tap="reload">查询</button>
      </view>
      <view class="list-actions"><text>共 {{ total }} 台设备</text><button v-if="canManage" @tap="openForm()">新增 OLT</button></view>
      <view v-if="items.length" class="device-groups">
        <view v-for="group in deviceGroups" :key="group.key" class="device-group">
          <view class="group-head" @tap="toggleGroup(group.key)">
            <view><view class="group-name">{{ group.name }}</view><view class="group-meta">{{ group.region }} · {{ group.items.length }} 台 OLT</view></view>
            <view class="group-toggle">{{ expandedGroups[group.key] === false ? '展开 ⌄' : '收起 ⌃' }}</view>
          </view>
          <view v-if="expandedGroups[group.key] !== false" class="device-list">
            <view v-for="item in group.items" :key="item.olt_device_id" class="device-card" @tap="openForm(item)">
              <view class="device-icon">OLT</view>
              <view class="device-main">
                <view class="device-head"><view class="device-name">{{ item.name || `OLT ${item.olt_device_id}` }}</view><StatusBadge :value="Number(item.is_active) === 1 ? 'active' : 'disabled'" /></view>
                <view class="device-ip">{{ item.primary_ip || '--' }}<text v-if="item.backup_ip"> / {{ item.backup_ip }}</text></view>
                <view class="device-meta">{{ item.room || '未标注机房' }}</view>
                <view class="device-foot"><text>{{ item.brand || '--' }} · {{ item.device_model || '--' }}</text><text>{{ item.community_configured ? 'SNMP 已配置' : '未配置 SNMP' }}</text></view>
              </view>
            </view>
          </view>
        </view>
      </view>
      <view v-else-if="loading" class="section-card"><view class="status-text">正在加载设备...</view></view>
      <EmptyState v-else mark="网" title="没有匹配的 OLT 设备" />
      <view v-if="items.length < total" class="load-more" @tap="loadMore">继续加载</view>
    </template>

    <template v-else>
      <view class="probe-card">
        <view class="probe-title">检测新 OLT</view>
        <view class="probe-sub">通过采集代理验证网络连通、SNMP、设备型号和样例数据。团体号只用于本次检测，不会自动入库。</view>
        <view class="field"><view class="field-label">OLT IP</view><input v-model="probe.ip" class="input" placeholder="例如 192.168.1.10" /></view>
        <view class="field"><view class="field-label">SNMP 团体号</view><input v-model="probe.community" class="input" password placeholder="输入团体号" /></view>
        <button class="primary-button" :loading="probeLoading" @tap="runProbe">开始检测</button>
      </view>
      <view v-if="probeResult" class="section-card probe-result">
        <view class="section-head"><view class="section-head-title">检测结果</view><StatusBadge :value="probeResult.success === false ? 'failed' : 'success'" /></view>
        <view class="result-grid">
          <view v-for="item in probeFields" :key="item.label"><text>{{ item.label }}</text><strong>{{ item.value || '--' }}</strong></view>
        </view>
        <view class="raw-result" @tap="copyProbeResult">复制完整检测结果</view>
      </view>
    </template>

    <view v-if="formVisible" class="overlay" @tap="formVisible = false">
      <view class="form-sheet" @tap.stop>
        <view class="sheet-head"><view class="sheet-title">{{ form.olt_device_id ? '编辑 OLT' : '新增 OLT' }}</view><view class="sheet-close" @tap="formVisible = false">×</view></view>
        <scroll-view scroll-y class="form-scroll">
          <view class="form-grid">
            <view class="field full"><view class="field-label">设备名称</view><input v-model="form.name" class="input" placeholder="设备名称" /></view>
            <view class="field"><view class="field-label">主 IP</view><input v-model="form.primary_ip" class="input" placeholder="主 IP" /></view>
            <view class="field"><view class="field-label">备用 IP</view><input v-model="form.backup_ip" class="input" placeholder="可选" /></view>
            <view class="field"><view class="field-label">区域</view><input v-model="form.region" class="input" placeholder="区域编码" /></view>
            <view class="field"><view class="field-label">机房组</view><input v-model="form.room_group" class="input" placeholder="机房组" /></view>
            <view class="field"><view class="field-label">机房</view><input v-model="form.room" class="input" placeholder="机房" /></view>
            <view class="field"><view class="field-label">品牌</view><input v-model="form.brand" class="input" placeholder="品牌" /></view>
            <view class="field full"><view class="field-label">设备型号</view><input v-model="form.device_model" class="input" placeholder="设备型号" /></view>
            <view class="field full"><view class="field-label">SNMP 团体号</view><input v-model="form.community" class="input" password :placeholder="form.olt_device_id ? '不修改请留空' : '请输入团体号'" /></view>
          </view>
          <view class="switch-row"><text>启用设备</text><switch :checked="Number(form.is_active) === 1" color="#2269c8" @change="form.is_active = $event.detail.value ? 1 : 0" /></view>
          <button class="primary-button save-button" :loading="saving" @tap="saveDevice">保存设备</button>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad, onReachBottom } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import StatusBadge from '../../../components/netops/StatusBadge.vue'
import { createOltDevice, getOltDevices, probeOlt, updateOltDevice } from '../../../api/netops'
import { getStoredUser } from '../../../api/auth'
import { messageLabel } from '../../../utils/labels'

const tab = ref('list')
const keyword = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const formVisible = ref(false)
const saving = ref(false)
const form = reactive(emptyForm())
const probe = reactive({ ip: '', community: '' })
const probeResult = ref(null)
const probeLoading = ref(false)
const canManage = computed(() => ['super_admin', 'org_admin'].includes(getStoredUser().role_code))
const expandedGroups = ref({})
const deviceGroups = computed(() => {
  const groups = new Map()
  items.value.forEach((item) => {
    const region = item.region || '未分区域'
    const roomGroup = item.room_group || '未分机房组'
    const key = `${region}::${roomGroup}`
    if (!groups.has(key)) groups.set(key, { key, region, name: roomGroup, items: [] })
    groups.get(key).items.push(item)
  })
  return Array.from(groups.values())
})
const probeFields = computed(() => {
  const result = probeResult.value || {}
  return [
    { label: 'Ping', value: displayFlag(result.is_ping ?? result.ping) }, { label: 'SNMP', value: displayFlag(result.is_snmp ?? result.snmp) },
    { label: '厂商', value: result.brand || result.vendor }, { label: '型号', value: result.device_model || result.model },
    { label: '版本', value: result.version || result.software_version }, { label: '接口数', value: result.if_cnt || result.interface_count }
  ]
})

onLoad(reload)
onReachBottom(loadMore)

function emptyForm() { return { olt_device_id: null, name: '', primary_ip: '', backup_ip: '', region: '', room_group: '', room: '', brand: '', device_model: '', community: '', is_active: 1 } }
function reload() { page.value = 1; items.value = []; loadData() }
function toggleGroup(key) { expandedGroups.value = { ...expandedGroups.value, [key]: expandedGroups.value[key] === false } }
function loadMore() { if (!loading.value && items.value.length < total.value) { page.value += 1; loadData(true) } }
function loadData(append = false) {
  loading.value = true
  getOltDevices({ keyword: keyword.value.trim(), page: page.value, size: 30 })
    .then((data) => { items.value = append ? items.value.concat(data.items || []) : (data.items || []); total.value = Number(data.total || 0) })
    .catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' }))
    .finally(() => { loading.value = false })
}
function openForm(item) {
  if (item && !canManage.value) return
  Object.assign(form, emptyForm(), item || {}, { community: '' })
  formVisible.value = true
}
function saveDevice() {
  if (!form.name.trim() || !form.primary_ip.trim()) return uni.showToast({ title: '设备名称和主 IP 必填', icon: 'none' })
  saving.value = true
  const payload = { ...form }
  if (form.olt_device_id && !payload.community) delete payload.community
  const action = form.olt_device_id ? updateOltDevice(form.olt_device_id, payload) : createOltDevice(payload)
  action.then(() => { formVisible.value = false; uni.showToast({ title: '保存成功', icon: 'success' }); reload() }).catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' })).finally(() => { saving.value = false })
}
function runProbe() {
  if (!probe.ip.trim() || !probe.community.trim()) return uni.showToast({ title: '请输入 IP 和团体号', icon: 'none' })
  probeLoading.value = true; probeResult.value = null
  probeOlt({ ip: probe.ip.trim(), community: probe.community.trim() }).then((data) => { probeResult.value = data }).catch((error) => uni.showToast({ title: messageLabel(error.message), icon: 'none' })).finally(() => { probeLoading.value = false })
}
function copyProbeResult() { uni.setClipboardData({ data: JSON.stringify(probeResult.value, null, 2) }) }
function displayFlag(value) { return value === true || Number(value) === 1 ? '正常' : value === false || Number(value) === 0 ? '失败' : value || '--' }
</script>

<style scoped>
.device-groups{display:flex;flex-direction:column;gap:16rpx}.device-group{overflow:hidden;border:1rpx solid #e1e7ee;border-radius:18rpx;background:#fff}.group-head{display:flex;align-items:center;justify-content:space-between;padding:22rpx 24rpx;background:#f5f8fb}.group-name{color:#26374b;font-size:26rpx;font-weight:750}.group-meta{margin-top:5rpx;color:#8491a0;font-size:19rpx}.group-toggle{color:#376fa8;font-size:20rpx}.device-group .device-list{padding:0 22rpx}
.tab-bar{display:flex;margin-bottom:16rpx;padding:7rpx;border-radius:14rpx;background:#e7edf3}.tab{flex:1;padding:16rpx;border-radius:10rpx;color:#6a788a;font-size:23rpx;text-align:center}.tab.active{background:#fff;color:#255f9e;font-weight:700}.list-actions{display:flex;align-items:center;justify-content:space-between;margin:18rpx 2rpx;color:#788596;font-size:22rpx}.list-actions button{padding:12rpx 18rpx;border-radius:11rpx;background:#2269c8;color:#fff;font-size:22rpx}.device-list{display:flex;flex-direction:column;gap:14rpx}.device-card{display:flex;gap:18rpx;padding:22rpx;border:1rpx solid #e2e8ef;border-radius:17rpx;background:#fff}.device-icon{display:flex;align-items:center;justify-content:center;width:74rpx;height:74rpx;flex:none;border-radius:17rpx;background:#eaf2fc;color:#2867ae;font-size:20rpx;font-weight:750}.device-main{min-width:0;flex:1}.device-head{display:flex;align-items:center;justify-content:space-between;gap:12rpx}.device-name{overflow:hidden;color:#223247;font-size:26rpx;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.device-ip{margin-top:8rpx;color:#396184;font-family:monospace;font-size:22rpx}.device-meta{margin-top:7rpx;color:#7c8999;font-size:20rpx}.device-foot{display:flex;justify-content:space-between;gap:14rpx;margin-top:12rpx;color:#929ca9;font-size:18rpx}.probe-card{padding:28rpx;border:1rpx solid #e1e7ee;border-radius:19rpx;background:#fff}.probe-title{color:#223247;font-size:31rpx;font-weight:750}.probe-sub{margin-top:9rpx;color:#788596;font-size:22rpx;line-height:1.55}.field{margin-top:22rpx}.probe-card .primary-button{margin-top:26rpx}.probe-result{margin-top:20rpx}.result-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1rpx;background:#e8edf2}.result-grid view{padding:20rpx;background:#fff}.result-grid text{display:block;color:#8793a1;font-size:20rpx}.result-grid strong{display:block;margin-top:7rpx;color:#2f4055;font-size:23rpx}.raw-result{padding:22rpx;color:#2b67aa;font-size:22rpx;text-align:center}.overlay{position:fixed;z-index:20;inset:0;display:flex;align-items:flex-end;background:rgba(18,28,40,.46)}.form-sheet{width:100%;height:82vh;border-radius:28rpx 28rpx 0 0;background:#f4f7fa}.sheet-head{display:flex;align-items:center;justify-content:space-between;padding:25rpx 28rpx 16rpx}.sheet-title{font-size:31rpx;font-weight:750}.sheet-close{font-size:44rpx;color:#7e8a99}.form-scroll{height:calc(82vh - 88rpx);padding:0 24rpx 40rpx;box-sizing:border-box}.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:0 16rpx}.field.full{grid-column:1/-1}.switch-row{display:flex;align-items:center;justify-content:space-between;margin-top:22rpx;padding:18rpx 20rpx;border-radius:12rpx;background:#fff;font-size:24rpx}.save-button{margin-top:24rpx}
</style>
