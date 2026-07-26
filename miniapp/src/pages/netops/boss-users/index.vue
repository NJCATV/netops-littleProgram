<template>
  <view class="netops-page boss-page">
    <view v-if="!unlocked" class="unlock-card">
      <view class="shield">密</view>
      <view class="unlock-title">BOSS 敏感资料二次验证</view>
      <view class="unlock-desc">仅超级管理员可访问。验证当前小程序登录密码后开放 5 分钟，所有查询和详情访问都会写入审计日志。</view>
      <input v-model="password" class="input password-input" password placeholder="请输入当前登录密码" confirm-type="done" @confirm="unlock" />
      <button class="primary-button" :loading="unlocking" @tap="unlock">验证并进入</button>
    </view>

    <template v-else>
      <view class="security-strip"><text>敏感访问已授权</text><text>{{ remainMinutes }} 分钟后自动锁定</text></view>
      <view class="search-bar"><input v-model="keyword" class="search-input" placeholder="至少4位：GDF账号、姓名、地址、ONU MAC" confirm-type="search" @confirm="reload" /><button class="search-button" @tap="reload">查询</button></view>
      <view class="result-meta"><text>{{ searched ? `共找到 ${total} 条脱敏资料` : '不会自动加载或批量暴露用户资料' }}</text><button @tap="chooseImport">导入 Excel</button></view>
      <view v-if="items.length" class="user-list">
        <view v-for="item in items" :key="item.id" class="user-card" @tap="openDetail(item)">
          <view class="user-head"><view><view class="user-name">{{ item.name || '未登记姓名' }}</view><view class="user-account">{{ item.id_number || '--' }}</view></view><view class="mac-tag">{{ item.display_mac || formatMac(item.onu_mac_norm) }}</view></view>
          <view class="info-row"><text>区域网格</text><text>{{ item.region || '--' }} / {{ item.grid || '--' }}</text></view>
          <view class="info-row"><text>联系电话</text><text>{{ [item.phone1, item.phone2].filter(Boolean).join(' / ') || '--' }}</text></view>
          <view class="address">{{ item.address || '未登记装机地址' }}</view>
          <view class="user-foot"><text>最近更新 {{ item.visit_datetime || '--' }}</text><text class="query-link">验证授权内查看详情 ›</text></view>
        </view>
      </view>
      <view v-else-if="loading" class="section-card"><view class="status-text">正在安全查询 BOSS 用户...</view></view>
      <EmptyState v-else :mark="searched ? '客' : '锁'" :title="searched ? '没有找到用户资料' : '输入明确条件后查询'" description="列表仅返回脱敏字段，完整资料需要逐条打开并记录审计。" />
      <view v-if="items.length < total" class="load-more" @tap="loadMore">{{ loading ? '加载中...' : '继续加载' }}</view>
    </template>

    <view v-if="detail" class="overlay" @tap="detail = null">
      <view class="detail-sheet" @tap.stop>
        <view class="sheet-head"><view><view class="sheet-kicker">BOSS 用户详情 · 已审计</view><view class="sheet-title">{{ detail.name || '未登记姓名' }}</view></view><view class="sheet-close" @tap="detail = null">×</view></view>
        <view class="detail-grid">
          <view><text>GDF 账号</text><strong>{{ detail.id_number || '--' }}</strong></view>
          <view><text>ONU MAC</text><strong>{{ detail.display_mac || formatMac(detail.onu_mac_norm) }}</strong></view>
          <view><text>联系电话</text><strong>{{ [detail.phone1, detail.phone2].filter(Boolean).join(' / ') || '--' }}</strong></view>
          <view><text>区域 / 网格</text><strong>{{ detail.region || '--' }} / {{ detail.grid || '--' }}</strong></view>
          <view class="full"><text>所属公司</text><strong>{{ detail.company || '--' }}</strong></view>
          <view class="full"><text>装机地址</text><strong>{{ detail.address || '--' }}</strong></view>
        </view>
        <button class="primary-button" @tap="openOnu(detail)">查询关联 ONU</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onHide, onLoad, onReachBottom, onUnload } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import { createBossAccess, getBossUserDetail, getBossUsers, importBossUsers } from '../../../api/netops'
import { getStoredUser } from '../../../api/auth'
import { messageLabel } from '../../../utils/labels'

const password=ref(''),accessToken=ref(''),expiresAt=ref(0),keyword=ref(''),items=ref([]),total=ref(0),page=ref(1),loading=ref(false),unlocking=ref(false),searched=ref(false),detail=ref(null)
const unlocked=computed(()=>Boolean(accessToken.value)&&expiresAt.value>Math.floor(Date.now()/1000))
const remainMinutes=computed(()=>Math.max(1,Math.ceil((expiresAt.value-Math.floor(Date.now()/1000))/60)))

onLoad(()=>{if(getStoredUser().role_code!=='super_admin'){uni.showToast({title:'仅超级管理员可访问',icon:'none'});setTimeout(()=>uni.navigateBack(),500)}})
onReachBottom(loadMore)
onHide(clearSensitiveState)
onUnload(clearSensitiveState)

function unlock(){if(!password.value)return uni.showToast({title:'请输入当前登录密码',icon:'none'});unlocking.value=true;createBossAccess(password.value).then(data=>{accessToken.value=data.access_token||'';expiresAt.value=Number(data.expires_at||0);password.value='';uni.showToast({title:'验证通过',icon:'success'})}).catch(error=>uni.showToast({title:messageLabel(error.message),icon:'none'})).finally(()=>{unlocking.value=false})}
function ensureAccess(){if(unlocked.value)return true;clearSensitiveState();uni.showToast({title:'敏感访问已锁定，请重新验证',icon:'none'});return false}
function reload(){if(!ensureAccess())return;if(keyword.value.trim().length<4)return uni.showToast({title:'请输入至少 4 个字符',icon:'none'});page.value=1;items.value=[];searched.value=true;loadData()}
function loadMore(){if(unlocked.value&&!loading.value&&items.value.length<total.value){page.value+=1;loadData(true)}}
function loadData(append=false){loading.value=true;getBossUsers({keyword:keyword.value.trim(),page:page.value,size:20},accessToken.value).then(data=>{items.value=append?items.value.concat(data.items||[]):(data.items||[]);total.value=Number(data.total||0)}).catch(handleSensitiveError).finally(()=>{loading.value=false})}
function openDetail(item){if(!ensureAccess())return;uni.showLoading({title:'读取敏感详情'});getBossUserDetail(item.id,accessToken.value).then(data=>{detail.value=data}).catch(handleSensitiveError).finally(()=>uni.hideLoading())}
function openOnu(item){const value=item.onu_mac_norm||item.id_number;if(!value)return;detail.value=null;const type=item.onu_mac_norm?'mac':'account';uni.navigateTo({url:`/pages/netops/onu/index?type=${type}&keyword=${encodeURIComponent(value)}`})}
function chooseImport(){if(!ensureAccess())return;const token=accessToken.value;uni.chooseMessageFile({count:1,type:'file',extension:['xlsx'],success(result){const file=result.tempFiles?.[0];if(!file)return;uni.showModal({title:'导入 BOSS 用户',content:`确认导入“${file.name}”？该操作会写入审计日志。`,success(modal){if(modal.confirm)runImport(file.path,token)}})}})}
function runImport(filePath,token){uni.showLoading({title:'正在导入'});importBossUsers(filePath,token).then(data=>{uni.hideLoading();uni.showModal({title:'导入完成',content:`有效 ${data.valid_rows||0} 行，新增 ${data.inserted||0}，更新 ${data.updated||0}，跳过 ${data.skipped||0}`})}).catch(error=>{uni.hideLoading();handleSensitiveError(error)})}
function handleSensitiveError(error){if(/授权|权限|密码|403/.test(error.message||''))clearSensitiveState();uni.showToast({title:messageLabel(error.message),icon:'none'})}
function clearSensitiveState(){password.value='';accessToken.value='';expiresAt.value=0;items.value=[];total.value=0;detail.value=null;searched.value=false}
function formatMac(value){return String(value||'').replace(/(.{2})(?=.)/g,'$1:').toUpperCase()||'--'}
</script>

<style scoped>
.unlock-card{margin-top:36rpx;padding:38rpx 30rpx;border:1rpx solid #dfe6ee;border-radius:22rpx;background:#fff;text-align:center}.shield{display:flex;align-items:center;justify-content:center;width:82rpx;height:82rpx;margin:0 auto;border-radius:24rpx;background:#273e5c;color:#fff;font-size:30rpx;font-weight:750}.unlock-title{margin-top:22rpx;color:#203047;font-size:30rpx;font-weight:750}.unlock-desc{margin-top:13rpx;color:#738194;font-size:21rpx;line-height:1.6}.password-input{margin-top:28rpx;text-align:left}.unlock-card .primary-button{margin-top:18rpx}.security-strip{display:flex;justify-content:space-between;margin-bottom:16rpx;padding:14rpx 18rpx;border-radius:12rpx;background:#eaf6f0;color:#237257;font-size:20rpx}.result-meta{display:flex;align-items:center;justify-content:space-between;margin:17rpx 4rpx;color:#7c8999;font-size:21rpx}.result-meta button{padding:10rpx 15rpx;border-radius:9rpx;background:#eaf3fe;color:#2d69a9;font-size:20rpx}.user-list{display:flex;flex-direction:column;gap:14rpx}.user-card{padding:24rpx;border:1rpx solid #e1e7ee;border-radius:17rpx;background:#fff}.user-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18rpx}.user-name{color:#24354a;font-size:27rpx;font-weight:700}.user-account{margin-top:5rpx;color:#718094;font-size:21rpx}.mac-tag{padding:8rpx 12rpx;border-radius:9rpx;background:#edf4fc;color:#356796;font-family:monospace;font-size:19rpx}.info-row{display:flex;justify-content:space-between;gap:20rpx;margin-top:15rpx;color:#788596;font-size:21rpx}.info-row text:last-child{color:#4d5d72;text-align:right}.address{margin-top:15rpx;padding:14rpx;border-radius:10rpx;background:#f6f8fa;color:#647285;font-size:20rpx;line-height:1.5}.user-foot{display:flex;justify-content:space-between;gap:16rpx;margin-top:16rpx;color:#98a1ad;font-size:19rpx}.query-link{color:#2f6fae}.overlay{position:fixed;z-index:30;inset:0;display:flex;align-items:flex-end;background:rgba(18,28,40,.5)}.detail-sheet{width:100%;padding:28rpx 26rpx 44rpx;border-radius:28rpx 28rpx 0 0;background:#f4f7fa;box-sizing:border-box}.sheet-head{display:flex;align-items:flex-start;justify-content:space-between}.sheet-kicker{color:#7e8997;font-size:20rpx}.sheet-title{margin-top:6rpx;color:#213249;font-size:32rpx;font-weight:750}.sheet-close{padding:0 8rpx;color:#7e8997;font-size:44rpx}.detail-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1rpx;margin:22rpx 0;overflow:hidden;border:1rpx solid #e2e8ef;border-radius:15rpx;background:#e2e8ef}.detail-grid view{min-width:0;padding:19rpx;background:#fff}.detail-grid .full{grid-column:1/-1}.detail-grid text,.detail-grid strong{display:block}.detail-grid text{color:#8793a2;font-size:19rpx}.detail-grid strong{margin-top:7rpx;color:#324257;font-size:22rpx;line-height:1.45;word-break:break-all}
</style>
