<template>
  <view class="netops-page">
    <view class="tab-bar"><view v-for="item in tabs" :key="item.value" class="tab" :class="{ active: tab===item.value }" @tap="tab=item.value">{{ item.label }}</view></view>

    <template v-if="tab==='orgs'">
      <view class="intro-card"><view><strong>设备组织</strong><text>维护网管侧区域与机房层级</text></view><button v-if="canManage" @tap="openOrgForm()">新增</button></view>
      <view class="org-list">
        <view v-for="region in regions" :key="region.id" class="region-card">
          <view class="region-row" @tap="toggleRegion(region.id)"><view class="expand">{{ expanded.includes(region.id)?'−':'+' }}</view><view class="region-main"><strong>{{ region.name }}</strong><text>{{ region.region_code }} · {{ region.device_count||0 }} 台 OLT</text></view><view v-if="canManage" class="more" @tap.stop="orgActions(region)">•••</view></view>
          <view v-if="expanded.includes(region.id)" class="room-list"><view v-for="room in children(region.id)" :key="room.id" class="room-row"><view class="branch">└</view><view><strong>{{ room.name }}</strong><text>{{ room.device_count||0 }} 台设备</text></view><view v-if="canManage" class="more" @tap="orgActions(room)">•••</view></view><view v-if="canManage" class="add-room" @tap="openOrgForm(null,region)">+ 添加机房</view></view>
        </view>
      </view>
      <EmptyState v-if="!regions.length" mark="域" title="暂无设备组织" />
    </template>

    <template v-else-if="tab==='mapping'">
      <view class="intro-card"><view><strong>组织区域映射</strong><text>控制用户组织可查看的设备区域</text></view></view>
      <view class="mapping-list">
        <view v-for="item in mappings" :key="item.user_org_id" class="mapping-card"><view class="mapping-head"><strong>{{ item.user_org_name }}</strong><button @tap="editMapping(item)">配置</button></view><view class="tags"><text v-for="code in item.regions" :key="code">{{ regionName(code) }}</text><text v-if="!item.regions.length" class="empty-tag">未分配区域</text></view></view>
      </view>
      <EmptyState v-if="!mappings.length" mark="权" title="暂无可配置映射" description="仅系统管理员可以维护跨域映射。" />
    </template>

    <template v-else>
      <view class="rule-card"><view class="rule-title">ONU 接收光功率规则</view><view class="rule-desc">低于或高于阈值时进入质差列表；无效范围用于排除设备异常值。</view><view class="rule-grid"><view v-for="field in qualityFields" :key="field.key" class="field"><view class="field-label">{{ field.label }}</view><input v-model="qualityRule[field.key]" class="input" type="digit" /></view></view><button v-if="canManage" class="primary-button" @tap="saveQuality">保存 ONU 规则</button></view>
      <view class="rule-card"><view class="rule-title">OLT 性能告警规则</view><view class="rule-desc">设备和板卡分别设置告警、严重阈值，并配置数据过期时间。</view><view class="rule-grid"><view v-for="field in performanceFields" :key="field.key" class="field"><view class="field-label">{{ field.label }}</view><input v-model="performanceRule[field.key]" class="input" type="digit" /></view></view><view class="switch-row"><text>将采集失败计入异常</text><switch :checked="performanceRule.include_collect_failures" color="#2269c8" @change="performanceRule.include_collect_failures=$event.detail.value" /></view><button v-if="canManage" class="primary-button" @tap="savePerformance">保存性能规则</button></view>
    </template>

    <view v-if="orgFormVisible" class="overlay" @tap="orgFormVisible=false"><view class="form-sheet compact" @tap.stop><view class="sheet-head"><view class="sheet-title">{{ orgForm.id?'编辑设备组织':'新增设备组织' }}</view><view class="sheet-close" @tap="orgFormVisible=false">×</view></view><view class="sheet-body"><view class="field"><view class="field-label">组织名称</view><input v-model="orgForm.name" class="input" /></view><view v-if="orgForm.node_type==='region'&&!orgForm.id" class="field"><view class="field-label">区域编码</view><input v-model="orgForm.region_code" class="input" placeholder="小写字母、数字、下划线" /></view><button class="primary-button save-button" @tap="saveOrg">保存</button></view></view></view>

    <view v-if="mappingVisible" class="overlay" @tap="mappingVisible=false"><view class="form-sheet compact" @tap.stop><view class="sheet-head"><view class="sheet-title">{{ currentMapping.user_org_name }}</view><view class="sheet-close" @tap="mappingVisible=false">×</view></view><view class="sheet-body"><checkbox-group @change="mappingSelection=$event.detail.value"><label v-for="region in mappingRegions" :key="region.code" class="check-row"><checkbox :value="region.code" :checked="mappingSelection.includes(region.code)" color="#2269c8" /><text>{{ region.name }}</text><text>{{ region.code }}</text></label></checkbox-group><button class="primary-button save-button" @tap="saveMapping">保存映射</button></view></view></view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import { createDeviceOrganization, deleteDeviceOrganization, getDeviceOrganizations, getNetopsSettings, getOrganizationMappings, saveOltPerformanceRule, saveOnuQualityRule, updateDeviceOrganization, updateOrganizationMapping } from '../../../api/netops'
import { getStoredUser } from '../../../api/auth'
import { messageLabel } from '../../../utils/labels'

const tabs=[{value:'orgs',label:'设备组织'},{value:'mapping',label:'区域权限'},{value:'rules',label:'告警规则'}]
const tab=ref('orgs'),orgs=ref([]),expanded=ref([]),mappings=ref([]),mappingRegions=ref([]),orgFormVisible=ref(false),mappingVisible=ref(false),mappingSelection=ref([]),currentMapping=ref({})
const orgForm=reactive({id:null,parent_id:null,node_type:'region',region_code:'',name:'',sort_order:0})
const qualityRule=reactive({}),performanceRule=reactive({})
const canManage=computed(()=>['super_admin','org_admin'].includes(getStoredUser().role_code))
const regions=computed(()=>orgs.value.filter(item=>item.node_type==='region'))
const qualityFields=[{key:'onu_rx_low_dbm',label:'低光阈值 dBm'},{key:'onu_rx_high_dbm',label:'高光阈值 dBm'},{key:'onu_rx_invalid_min_dbm',label:'无效最小值'},{key:'onu_rx_invalid_max_dbm',label:'无效最大值'}]
const performanceFields=[{key:'olt_cpu_warning',label:'OLT CPU 告警 %'},{key:'olt_cpu_critical',label:'OLT CPU 严重 %'},{key:'olt_mem_warning',label:'OLT 内存告警 %'},{key:'olt_mem_critical',label:'OLT 内存严重 %'},{key:'board_cpu_warning',label:'板卡 CPU 告警 %'},{key:'board_cpu_critical',label:'板卡 CPU 严重 %'},{key:'board_mem_warning',label:'板卡内存告警 %'},{key:'board_mem_critical',label:'板卡内存严重 %'},{key:'stale_minutes',label:'采集过期分钟'}]

onLoad(()=>{loadOrgs();loadMappings();loadSettings()})
function children(id){return orgs.value.filter(item=>Number(item.parent_id)===Number(id))}
function toggleRegion(id){expanded.value=expanded.value.includes(id)?expanded.value.filter(item=>item!==id):expanded.value.concat(id)}
function loadOrgs(){getDeviceOrganizations().then(data=>{orgs.value=data.items||[]}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}
function loadMappings(){getOrganizationMappings().then(data=>{mappings.value=data.items||[];mappingRegions.value=data.regions||[]}).catch(()=>{mappings.value=[]})}
function loadSettings(){getNetopsSettings().then(data=>{Object.assign(qualityRule,data.quality?.onu_rx_rule||{});Object.assign(performanceRule,data.performance?.olt_rule||{})}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}
function openOrgForm(item,parent){Object.assign(orgForm,{id:item?.id||null,parent_id:parent?.id||item?.parent_id||null,node_type:item?.node_type||(parent?'room':'region'),region_code:item?.region_code||parent?.region_code||'',name:item?.name||'',sort_order:item?.sort_order||0});orgFormVisible.value=true}
function orgActions(item){uni.showActionSheet({itemList:['编辑','删除'],success(result){if(result.tapIndex===0)openOrgForm(item);else confirmDelete(item)}})}
function confirmDelete(item){uni.showModal({title:'删除设备组织',content:`确认删除“${item.name}”？组织下有设备时后端会拒绝删除。`,success(result){if(result.confirm)deleteDeviceOrganization(item.id).then(()=>{uni.showToast({title:'已删除',icon:'success'});loadOrgs()}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}})}
function saveOrg(){if(!orgForm.name.trim())return uni.showToast({title:'请输入组织名称',icon:'none'});const action=orgForm.id?updateDeviceOrganization(orgForm.id,{name:orgForm.name,sort_order:orgForm.sort_order}):createDeviceOrganization({...orgForm});action.then(()=>{orgFormVisible.value=false;uni.showToast({title:'保存成功',icon:'success'});loadOrgs()}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}
function editMapping(item){currentMapping.value=item;mappingSelection.value=[...(item.regions||[])];mappingVisible.value=true}
function saveMapping(){updateOrganizationMapping(currentMapping.value.user_org_id,{regions:mappingSelection.value}).then(()=>{mappingVisible.value=false;uni.showToast({title:'映射已更新',icon:'success'});loadMappings()}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}
function regionName(code){return mappingRegions.value.find(item=>item.code===code)?.name||code}
function saveQuality(){saveOnuQualityRule({...qualityRule}).then(data=>{Object.assign(qualityRule,data.onu_rx_rule||{});uni.showToast({title:'规则已保存',icon:'success'})}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}
function savePerformance(){saveOltPerformanceRule({...performanceRule}).then(data=>{Object.assign(performanceRule,data.olt_rule||{});uni.showToast({title:'规则已保存',icon:'success'})}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'}))}
</script>

<style scoped>
.tab-bar{display:flex;margin-bottom:18rpx;padding:7rpx;border-radius:14rpx;background:#e7edf3}.tab{flex:1;padding:16rpx 6rpx;border-radius:10rpx;color:#6a788a;font-size:22rpx;text-align:center}.tab.active{background:#fff;color:#255f9e;font-weight:700}.intro-card{display:flex;align-items:center;justify-content:space-between;gap:18rpx;margin-bottom:16rpx;padding:23rpx;border:1rpx solid #e2e8ef;border-radius:16rpx;background:#fff}.intro-card strong,.intro-card text{display:block}.intro-card strong{font-size:27rpx}.intro-card text{margin-top:6rpx;color:#8491a0;font-size:20rpx}.intro-card button,.mapping-head button{padding:11rpx 17rpx;border-radius:10rpx;background:#eaf3fe;color:#2866aa;font-size:21rpx}.org-list,.mapping-list{display:flex;flex-direction:column;gap:13rpx}.region-card,.mapping-card{overflow:hidden;border:1rpx solid #e1e7ee;border-radius:16rpx;background:#fff}.region-row,.room-row{display:flex;align-items:center;gap:15rpx;padding:21rpx}.expand{display:flex;align-items:center;justify-content:center;width:42rpx;height:42rpx;border-radius:9rpx;background:#edf3f9;color:#376a9d;font-size:27rpx}.region-main,.room-row>view:nth-child(2){min-width:0;flex:1}.region-main strong,.region-main text,.room-row strong,.room-row text{display:block}.region-main strong,.room-row strong{font-size:24rpx}.region-main text,.room-row text{margin-top:5rpx;color:#8793a2;font-size:19rpx}.more{padding:12rpx;color:#7f8b99}.room-list{border-top:1rpx solid #edf1f5;background:#fafbfd}.room-row{padding-left:34rpx;border-bottom:1rpx solid #edf1f5}.branch{color:#a2abb6}.add-room{padding:18rpx 34rpx;color:#2e6dac;font-size:21rpx}.mapping-card{padding:22rpx}.mapping-head{display:flex;align-items:center;justify-content:space-between}.mapping-head strong{font-size:25rpx}.tags{display:flex;flex-wrap:wrap;gap:9rpx;margin-top:15rpx}.tags text{padding:8rpx 12rpx;border-radius:8rpx;background:#edf4fc;color:#376a9d;font-size:19rpx}.tags .empty-tag{background:#f2f4f6;color:#8b96a4}.rule-card{margin-bottom:18rpx;padding:25rpx;border:1rpx solid #e1e7ee;border-radius:17rpx;background:#fff}.rule-title{font-size:28rpx;font-weight:750}.rule-desc{margin-top:7rpx;color:#7d8999;font-size:21rpx;line-height:1.5}.rule-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:0 14rpx}.rule-card .primary-button{margin-top:24rpx}.switch-row{display:flex;align-items:center;justify-content:space-between;margin-top:20rpx;padding:15rpx 0;font-size:23rpx}.overlay{position:fixed;z-index:20;inset:0;display:flex;align-items:flex-end;background:rgba(18,28,40,.46)}.form-sheet.compact{width:100%;max-height:74vh;border-radius:28rpx 28rpx 0 0;background:#f4f7fa}.sheet-head{display:flex;align-items:center;justify-content:space-between;padding:25rpx 28rpx 16rpx}.sheet-title{font-size:30rpx;font-weight:750}.sheet-close{font-size:44rpx;color:#7e8a99}.sheet-body{padding:0 24rpx 36rpx}.field{margin-top:18rpx}.save-button{margin-top:24rpx}.check-row{display:flex;align-items:center;gap:14rpx;padding:18rpx 4rpx;border-bottom:1rpx solid #e5eaf0;color:#344459;font-size:23rpx}.check-row text:nth-child(2){flex:1}.check-row text:last-child{color:#8d98a5;font-size:19rpx}
</style>
