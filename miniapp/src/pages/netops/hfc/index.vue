<template>
  <view class="netops-page">
    <view class="tab-bar"><view class="tab" :class="{ active: tab === 'search' }" @tap="tab = 'search'">CM 查询</view><view class="tab" :class="{ active: tab === 'devices' }" @tap="switchDevices">CMTS 设备</view></view>
    <template v-if="tab === 'search'">
      <view class="search-bar"><input v-model="mac" class="search-input" placeholder="输入至少 6 位 CM MAC" confirm-type="search" @confirm="runSearch" /><button class="search-button" :loading="loading" @tap="runSearch">查询</button></view>
      <EmptyState v-if="!searched && !primary" mark="缆" title="查询 CM 信号状态" description="按 MAC 地址定位 CM、所属 CMTS、上下行端口与信号指标。" />
      <EmptyState v-else-if="!loading && !primary" mark="查" title="没有找到匹配的 CM" />
      <view v-if="primary" class="cm-card">
        <view class="cm-head"><view><view class="cm-label">当前主记录</view><view class="cm-mac">{{ primary.display_mac || formatMac(primary.mac_address) }}</view></view><StatusBadge :value="primary.cmts_active ? 'active' : 'disabled'" :text="primary.cmts_active ? 'CMTS 启用' : 'CMTS 停用'" /></view>
        <view class="signal-grid">
          <view><text>上行 SNR</text><strong>{{ metric(primary.snr, ' dB') }}</strong></view><view><text>上行电平</text><strong>{{ metric(primary.lvl, ' dBmV') }}</strong></view>
          <view><text>下行 SNR</text><strong>{{ metric(primary.down_snr, ' dB') }}</strong></view><view><text>下行电平</text><strong>{{ metric(primary.down_lvl, ' dBmV') }}</strong></view>
        </view>
        <view class="cm-info"><view><text>CM IP</text><strong>{{ primary.cm_ip || '--' }}</strong></view><view><text>CMTS</text><strong>{{ primary.cmts_name || '--' }}</strong></view><view><text>上行端口</text><strong>{{ primary.uplink_port || primary.if_index || '--' }}</strong></view><view><text>下行端口</text><strong>{{ primary.downstream_port || primary.down_if_index || '--' }}</strong></view><view class="full"><text>机房位置</text><strong>{{ primary.region || '--' }} / {{ primary.room_group || '--' }} / {{ primary.room || '--' }}</strong></view></view>
        <view class="cm-time">采集时间 {{ primary.query_time || '--' }} · 来源 {{ primary.collect_source || primary.external_database || '--' }}</view>
      </view>
      <view v-if="items.length > 1" class="section-card duplicate-card"><view class="section-head"><view class="section-head-title">疑似重复记录</view><view class="section-head-meta">{{ items.length - 1 }} 条</view></view><view v-for="item in items.slice(1)" :key="item.id" class="duplicate-row"><view><strong>{{ item.cmts_name || '--' }}</strong><text>{{ item.display_mac || formatMac(item.mac_address) }} · {{ item.query_time || '--' }}</text></view><view>SNR {{ metric(item.snr, '') }} / 电平 {{ metric(item.lvl, '') }}</view></view></view>
    </template>

    <template v-else>
      <view class="search-bar"><input v-model="keyword" class="search-input" placeholder="搜索 CMTS 名称、IP、机房" confirm-type="search" @confirm="loadDevices" /><button class="search-button" @tap="loadDevices">查询</button></view>
      <view class="list-title"><text>共 {{ total }} 台 CMTS</text><button v-if="canManage" @tap="openForm()">新增 CMTS</button></view>
      <view class="device-list">
        <view v-for="item in devices" :key="item.cmts_device_id" class="device-card" @tap="openForm(item)">
          <view class="device-icon">HFC</view><view class="device-main"><view class="device-head"><strong>{{ item.name || `CMTS ${item.cmts_device_id}` }}</strong><StatusBadge :value="Number(item.is_active) === 1 ? 'active' : 'disabled'" /></view><view class="device-ip">{{ item.primary_ip || '--' }}</view><view class="device-meta">{{ item.region || '--' }} / {{ item.room_group || '--' }} / {{ item.room || '--' }}</view><view class="device-foot"><text>{{ item.device_model || '--' }}</text><text>{{ item.cm_count || 0 }} 个 CM</text></view></view>
        </view>
      </view>
      <EmptyState v-if="!loading && !devices.length" mark="缆" title="暂无 CMTS 设备" />
    </template>

    <view v-if="formVisible" class="overlay" @tap="formVisible = false"><view class="form-sheet" @tap.stop><view class="sheet-head"><view class="sheet-title">{{ form.cmts_device_id ? '编辑 CMTS' : '新增 CMTS' }}</view><view class="sheet-close" @tap="formVisible = false">×</view></view><scroll-view scroll-y class="form-scroll"><view class="field"><view class="field-label">设备名称</view><input v-model="form.name" class="input" /></view><view class="field"><view class="field-label">主 IP</view><input v-model="form.primary_ip" class="input" /></view><view class="field"><view class="field-label">区域 / 机房组 / 机房</view><view class="triple"><input v-model="form.region" class="input" placeholder="区域" /><input v-model="form.room_group" class="input" placeholder="机房组" /><input v-model="form.room" class="input" placeholder="机房" /></view></view><view class="field"><view class="field-label">品牌 / 型号</view><view class="double"><input v-model="form.brand" class="input" placeholder="品牌" /><input v-model="form.device_model" class="input" placeholder="型号" /></view></view><view class="field"><view class="field-label">SNMP 团体号</view><input v-model="form.community" class="input" password :placeholder="form.cmts_device_id ? '不修改请留空' : ''" /></view><view class="switch-row"><text>启用设备</text><switch :checked="Number(form.is_active)===1" color="#2269c8" @change="form.is_active=$event.detail.value?1:0" /></view><button class="primary-button save-button" :loading="saving" @tap="saveDevice">保存设备</button></scroll-view></view></view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import StatusBadge from '../../../components/netops/StatusBadge.vue'
import { createCmtsDevice, getCmtsDevices, searchCm, updateCmtsDevice } from '../../../api/netops'
import { getStoredUser } from '../../../api/auth'
import { messageLabel } from '../../../utils/labels'

const tab=ref('search'),mac=ref(''),keyword=ref(''),loading=ref(false),searched=ref(false),primary=ref(null),items=ref([]),devices=ref([]),total=ref(0),formVisible=ref(false),saving=ref(false)
const form=reactive(emptyForm())
const canManage=computed(()=>['super_admin','org_admin'].includes(getStoredUser().role_code))
onLoad(()=>{})
function emptyForm(){return{cmts_device_id:null,name:'',primary_ip:'',backup_ip:'',region:'',room_group:'',room:'',brand:'',device_model:'',community:'',is_active:1}}
function runSearch(){if(!mac.value.trim())return uni.showToast({title:'请输入 CM MAC',icon:'none'});loading.value=true;searched.value=true;searchCm({mac:mac.value.trim()}).then(data=>{items.value=data.items||[];primary.value=data.primary||null}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'})).finally(()=>{loading.value=false})}
function switchDevices(){tab.value='devices';if(!devices.value.length)loadDevices()}
function loadDevices(){loading.value=true;getCmtsDevices({keyword:keyword.value.trim(),page:1,size:100}).then(data=>{devices.value=data.items||[];total.value=Number(data.total||0)}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'})).finally(()=>{loading.value=false})}
function openForm(item){if(item&&!canManage.value)return;Object.assign(form,emptyForm(),item||{},{community:''});formVisible.value=true}
function saveDevice(){if(!form.name||!form.primary_ip)return uni.showToast({title:'设备名称和主 IP 必填',icon:'none'});saving.value=true;const payload={...form};if(form.cmts_device_id&&!payload.community)delete payload.community;const action=form.cmts_device_id?updateCmtsDevice(form.cmts_device_id,payload):createCmtsDevice(payload);action.then(()=>{formVisible.value=false;uni.showToast({title:'保存成功',icon:'success'});loadDevices()}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'})).finally(()=>{saving.value=false})}
function formatMac(value){return String(value||'').replace(/(.{2})(?=.)/g,'$1:').toUpperCase()||'--'}
function metric(value,suffix){return value===null||value===undefined||value===''?'--':`${value}${suffix}`}
</script>

<style scoped>
.tab-bar{display:flex;margin-bottom:16rpx;padding:7rpx;border-radius:14rpx;background:#e7edf3}.tab{flex:1;padding:16rpx;border-radius:10rpx;color:#6a788a;font-size:23rpx;text-align:center}.tab.active{background:#fff;color:#255f9e;font-weight:700}.cm-card{margin-top:20rpx;padding:26rpx;border:1rpx solid #dfe6ee;border-radius:19rpx;background:#fff}.cm-head{display:flex;align-items:center;justify-content:space-between;gap:16rpx}.cm-label{color:#8994a2;font-size:20rpx}.cm-mac{margin-top:6rpx;font-family:monospace;color:#24354a;font-size:32rpx;font-weight:750}.signal-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1rpx;margin-top:22rpx;overflow:hidden;border-radius:14rpx;background:#dfe7ef}.signal-grid view{padding:21rpx;background:#f3f7fa;text-align:center}.signal-grid text,.cm-info text{display:block;color:#8491a0;font-size:20rpx}.signal-grid strong{display:block;margin-top:7rpx;color:#31506e;font-size:27rpx}.cm-info{display:grid;grid-template-columns:repeat(2,1fr);gap:18rpx;margin-top:22rpx}.cm-info .full{grid-column:1/-1}.cm-info strong{display:block;margin-top:6rpx;color:#314157;font-size:22rpx}.cm-time{margin-top:20rpx;color:#929ca9;font-size:19rpx}.duplicate-card{margin-top:20rpx}.duplicate-row{display:flex;justify-content:space-between;gap:18rpx;padding:20rpx 24rpx;border-bottom:1rpx solid #edf1f5;color:#5d6b7d;font-size:20rpx}.duplicate-row strong,.duplicate-row text{display:block}.duplicate-row text{margin-top:5rpx;color:#8a95a3}.list-title{display:flex;align-items:center;justify-content:space-between;margin:18rpx 2rpx;color:#788596;font-size:22rpx}.list-title button{padding:12rpx 18rpx;border-radius:11rpx;background:#2269c8;color:#fff;font-size:22rpx}.device-list{display:flex;flex-direction:column;gap:14rpx}.device-card{display:flex;gap:18rpx;padding:22rpx;border:1rpx solid #e2e8ef;border-radius:17rpx;background:#fff}.device-icon{display:flex;align-items:center;justify-content:center;width:72rpx;height:72rpx;flex:none;border-radius:17rpx;background:#f0ecff;color:#6d56c1;font-size:18rpx;font-weight:750}.device-main{min-width:0;flex:1}.device-head,.device-foot{display:flex;align-items:center;justify-content:space-between;gap:12rpx}.device-head strong{font-size:26rpx}.device-ip{margin-top:8rpx;color:#446785;font-family:monospace;font-size:22rpx}.device-meta{margin-top:6rpx;color:#7f8b9a;font-size:20rpx}.device-foot{margin-top:11rpx;color:#929ca8;font-size:18rpx}.overlay{position:fixed;z-index:20;inset:0;display:flex;align-items:flex-end;background:rgba(18,28,40,.46)}.form-sheet{width:100%;height:78vh;border-radius:28rpx 28rpx 0 0;background:#f4f7fa}.sheet-head{display:flex;align-items:center;justify-content:space-between;padding:25rpx 28rpx 16rpx}.sheet-title{font-size:31rpx;font-weight:750}.sheet-close{font-size:44rpx;color:#7e8a99}.form-scroll{height:calc(78vh - 88rpx);padding:0 24rpx 40rpx;box-sizing:border-box}.field{margin-top:20rpx}.double,.triple{display:flex;gap:12rpx}.double .input,.triple .input{min-width:0;flex:1}.switch-row{display:flex;align-items:center;justify-content:space-between;margin-top:22rpx;padding:18rpx 20rpx;border-radius:12rpx;background:#fff;font-size:24rpx}.save-button{margin-top:24rpx}
</style>
