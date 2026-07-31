<template>
  <view class="netops-page radius-page">
    <view class="intro">
      <view class="intro-kicker">RADIUS 360° 用户画像</view>
      <view class="intro-title">账号、终端和拨号问题一次查清</view>
      <view class="intro-desc">输入 GDF/GDC 账号或完整终端 MAC，汇总认证、流量、会话与异常线索。</view>
    </view>

    <view class="search-bar">
      <input v-model="keyword" class="search-input" placeholder="GDF 账号或终端 MAC" confirm-type="search" @confirm="search" />
      <button class="search-button" :loading="loading" @tap="search">诊断</button>
    </view>

    <view v-if="error" class="error-box">{{ error }}</view>
    <view v-if="loading" class="section-card"><view class="status-text">正在关联 Radius 认证、会话和流量数据...</view></view>
    <EmptyState v-else-if="!profile" mark="拨" title="等待一键诊断" description="支持带分隔符或连续 12 位的完整 MAC，也支持 GDF/GDC 业务账号。" />

    <template v-else>
      <view class="identity-card">
        <view class="identity-main">
          <view class="identity-label">主账号</view>
          <view class="identity-title">{{ primaryAccount || '未识别账号' }}</view>
          <view class="identity-meta">{{ primaryMac || '未识别终端 MAC' }}</view>
          <view class="identity-time">最近活动 {{ profile.identity?.last_seen || '--' }}</view>
        </view>
        <view class="health" :class="healthTone">
          <strong>{{ profile.health?.score ?? '--' }}</strong>
          <text>健康分</text>
          <text>{{ profile.health?.label || '待判断' }}</text>
        </view>
      </view>

      <view v-if="identityTags.length" class="tag-row">
        <text v-for="tag in identityTags" :key="tag" class="identity-tag">{{ tag }}</text>
      </view>

      <view class="metric-grid">
        <view class="metric"><text>认证成功率</text><strong>{{ acceptRate }}%</strong><small>{{ profile.summary?.accept_total || 0 }} / {{ profile.summary?.auth_total || 0 }}</small></view>
        <view class="metric"><text>24h 总流量</text><strong>{{ bytes(total24h) }}</strong><small>上 {{ bytes(profile.summary?.input_24h) }} / 下 {{ bytes(profile.summary?.output_24h) }}</small></view>
        <view class="metric"><text>会话 / MAC</text><strong>{{ profile.summary?.sessions || 0 }} / {{ profile.summary?.mac_count || 0 }}</strong><small>{{ profile.summary?.accounting_records || 0 }} 条计费记录</small></view>
        <view class="metric"><text>NAS 数量</text><strong>{{ profile.summary?.nas_count || 0 }}</strong><small>回退 {{ profile.summary?.rollback_count || 0 }} 次</small></view>
      </view>

      <view class="section-card">
        <view class="section-head"><view class="section-head-title">问题诊断</view><view class="section-head-meta">{{ issues.length }} 项</view></view>
        <view v-if="issues.length" class="issue-list">
          <view v-for="issue in issues" :key="issue.code || issue.title" class="issue-row" :class="issue.level">
            <view class="issue-mark">{{ issue.level === 'ok' ? '✓' : '!' }}</view>
            <view><strong>{{ issue.title || '诊断结论' }}</strong><text>{{ issue.detail || '--' }}</text></view>
          </view>
        </view>
        <EmptyState v-else mark="安" title="暂无异常线索" description="当前账号没有命中可展示的诊断规则。" />
      </view>

      <view class="section-card">
        <view class="section-head"><view class="section-head-title">快速结论</view></view>
        <view class="fact-list">
          <view><text>最近认证</text><strong>{{ profile.summary?.latest_auth_result || '--' }}</strong><small>{{ profile.summary?.latest_auth_reason || '无拒绝原因' }}</small></view>
          <view><text>认证时间</text><strong>{{ profile.summary?.latest_auth_time || '--' }}</strong></view>
          <view><text>最近 Accounting</text><strong>{{ profile.summary?.latest_accounting_time || '--' }}</strong></view>
          <view><text>30 天流量</text><strong>{{ bytes(total30d) }}</strong></view>
        </view>
      </view>

      <view v-if="profile.onu_consistency" class="section-card consistency">
        <view class="section-head"><view class="section-head-title">FTTH ONU 一致性核验</view></view>
        <view class="consistency-body">
          <strong>{{ profile.onu_consistency.status_label || '待核验' }}</strong>
          <text>拨号终端 {{ profile.onu_consistency.terminal_mac || '--' }}</text>
          <small>{{ profile.onu_consistency.mapping_source?.freshness || profile.onu_consistency.mapping_source?.label || '以可用 OLT 映射证据为准。' }}</small>
        </view>
      </view>

      <view class="section-card">
        <view class="section-head"><view class="section-head-title">最近会话</view><view class="section-head-meta">{{ sessions.length }} 条</view></view>
        <view v-if="sessions.length" class="session-list">
          <view v-for="row in sessions.slice(0, 10)" :key="`${row.acct_session_id}-${row.nas_ip}`" class="session-row">
            <view><strong>{{ row.acct_session_id || '未识别会话' }}</strong><text>{{ row.nas_ip || '--' }} · {{ row.mac_addr || '--' }}</text></view>
            <view class="session-side"><strong>{{ statusName(row.latest_status) }}</strong><text>{{ duration(row.session_seconds) }}</text><small>{{ bytes(Number(row.input_bytes || 0) + Number(row.output_bytes || 0)) }}</small></view>
          </view>
        </view>
        <EmptyState v-else mark="会" title="暂无会话记录" description="当前查询对象没有可展示的 Accounting 会话。" />
      </view>

      <button v-if="primaryAccount || primaryMac" class="onu-button" @tap="openOnu">联查 FTTH ONU</button>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import { getRadiusProfile } from '../../../api/radius'
import { messageLabel } from '../../../utils/labels'

const keyword = ref('')
const loading = ref(false)
const error = ref('')
const profile = ref(null)

const primaryAccount = computed(() => profile.value?.identity?.accounts?.[0] || '')
const primaryMac = computed(() => profile.value?.identity?.macs?.[0] || '')
const identityTags = computed(() => [...(profile.value?.identity?.accounts || []), ...(profile.value?.identity?.macs || [])])
const issues = computed(() => profile.value?.issues || [])
const sessions = computed(() => profile.value?.sessions || [])
const total24h = computed(() => Number(profile.value?.summary?.input_24h || 0) + Number(profile.value?.summary?.output_24h || 0))
const total30d = computed(() => Number(profile.value?.summary?.input_30d || 0) + Number(profile.value?.summary?.output_30d || 0))
const acceptRate = computed(() => {
  const total = Number(profile.value?.summary?.auth_total || 0)
  return total ? (Number(profile.value?.summary?.accept_total || 0) / total * 100).toFixed(1) : '0.0'
})
const healthTone = computed(() => {
  const score = Number(profile.value?.health?.score || 0)
  return score >= 80 ? 'good' : score >= 60 ? 'warn' : 'bad'
})

onLoad((options) => {
  if (options?.keyword) {
    keyword.value = decodeURIComponent(options.keyword)
    search()
  }
})

function search() {
  const value = keyword.value.trim()
  if (value.length < 4) {
    error.value = '请输入完整 GDF 账号或 MAC（至少 4 个字符）'
    return
  }
  loading.value = true
  error.value = ''
  profile.value = null
  getRadiusProfile(value)
    .then((data) => { profile.value = data })
    .catch((err) => { error.value = messageLabel(err.message) })
    .finally(() => { loading.value = false })
}

function openOnu() {
  const type = primaryAccount.value ? 'account' : 'terminal_mac'
  const value = primaryAccount.value || primaryMac.value
  uni.navigateTo({ url: `/pages/netops/onu/index?type=${type}&keyword=${encodeURIComponent(value)}` })
}

function bytes(value) {
  let size = Number(value || 0)
  for (const unit of ['B', 'KB', 'MB', 'GB', 'TB']) {
    if (size < 1024) return `${size.toFixed(unit === 'B' ? 0 : 1)} ${unit}`
    size /= 1024
  }
  return `${size.toFixed(1)} PB`
}
function duration(value) {
  const seconds = Number(value || 0)
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)} 分钟`
  return `${(seconds / 3600).toFixed(1)} 小时`
}
function statusName(value) { return ({ 1: '上线', 2: '下线', 3: '在线更新' })[Number(value)] || '状态未知' }
</script>

<style scoped>
.radius-page{padding-top:0}.intro{margin:0 -24rpx 22rpx;padding:38rpx 30rpx 36rpx;border-radius:0 0 30rpx 30rpx;background:linear-gradient(145deg,#173d4a,#256975);color:#fff}.intro-kicker{color:rgba(255,255,255,.58);font-size:19rpx;letter-spacing:2rpx}.intro-title{margin-top:10rpx;font-size:34rpx;font-weight:750;line-height:1.35}.intro-desc{margin-top:10rpx;color:rgba(255,255,255,.72);font-size:22rpx;line-height:1.55}.error-box{margin-top:18rpx;padding:18rpx 20rpx;border-radius:12rpx;background:#fdeceb;color:#b63f39;font-size:23rpx}.identity-card{display:flex;align-items:center;gap:20rpx;margin-top:20rpx;padding:26rpx;border:1rpx solid #dce6ea;border-radius:20rpx;background:#fff}.identity-main{min-width:0;flex:1}.identity-label{color:#7d8997;font-size:20rpx}.identity-title{margin-top:7rpx;overflow:hidden;color:#1d3442;font-size:32rpx;font-weight:750;text-overflow:ellipsis;white-space:nowrap}.identity-meta{margin-top:8rpx;color:#2b6973;font-family:monospace;font-size:23rpx}.identity-time{margin-top:7rpx;color:#8995a3;font-size:20rpx}.health{display:flex;width:112rpx;height:112rpx;flex:none;flex-direction:column;align-items:center;justify-content:center;border:8rpx solid #d8eee7;border-radius:50%;color:#147356}.health.warn{border-color:#f2dfbd;color:#9d641c}.health.bad{border-color:#f1c9c6;color:#b8423c}.health strong{font-size:31rpx}.health text{font-size:17rpx}.tag-row{display:flex;gap:10rpx;margin:14rpx 0 20rpx;flex-wrap:wrap}.identity-tag{padding:8rpx 13rpx;border-radius:99rpx;background:#e8f3f3;color:#28636b;font-size:19rpx}.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14rpx;margin-bottom:20rpx}.metric{min-width:0;padding:22rpx;border:1rpx solid #e1e8ee;border-radius:17rpx;background:#fff}.metric text,.metric strong,.metric small{display:block}.metric text{color:#778493;font-size:20rpx}.metric strong{margin-top:9rpx;color:#203446;font-size:29rpx}.metric small{margin-top:6rpx;overflow:hidden;color:#8d98a4;font-size:18rpx;text-overflow:ellipsis;white-space:nowrap}.issue-list{padding:6rpx 24rpx 18rpx}.issue-row{display:flex;gap:16rpx;padding:19rpx 0;border-bottom:1rpx solid #edf1f4}.issue-row:last-child{border-bottom:0}.issue-mark{display:flex;width:38rpx;height:38rpx;flex:none;align-items:center;justify-content:center;border-radius:50%;background:#fff0df;color:#ad6919;font-size:21rpx;font-weight:750}.issue-row.ok .issue-mark{background:#e6f5ef;color:#16775d}.issue-row>view:last-child{min-width:0}.issue-row strong,.issue-row text{display:block}.issue-row strong{color:#2b3c4d;font-size:24rpx}.issue-row text{margin-top:7rpx;color:#6e7b8a;font-size:21rpx;line-height:1.55}.fact-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.fact-list>view{min-width:0;padding:21rpx 24rpx;border-right:1rpx solid #edf1f4;border-bottom:1rpx solid #edf1f4}.fact-list>view:nth-child(2n){border-right:0}.fact-list>view:nth-last-child(-n+2){border-bottom:0}.fact-list text,.fact-list strong,.fact-list small{display:block}.fact-list text{color:#82909f;font-size:19rpx}.fact-list strong{margin-top:7rpx;color:#2d3e51;font-size:22rpx;line-height:1.45}.fact-list small{margin-top:4rpx;color:#9a675b;font-size:18rpx}.consistency-body{padding:22rpx 24rpx}.consistency-body strong,.consistency-body text,.consistency-body small{display:block}.consistency-body strong{color:#215f69;font-size:26rpx}.consistency-body text{margin-top:9rpx;color:#42566a;font-size:22rpx}.consistency-body small{margin-top:8rpx;color:#7f8b98;font-size:20rpx;line-height:1.5}.session-list{padding:0 24rpx}.session-row{display:flex;align-items:center;justify-content:space-between;gap:18rpx;padding:20rpx 0;border-bottom:1rpx solid #edf1f4}.session-row:last-child{border-bottom:0}.session-row>view:first-child{min-width:0;flex:1}.session-row strong,.session-row text,.session-row small{display:block}.session-row>view:first-child strong{overflow:hidden;color:#2c3c4d;font-size:22rpx;text-overflow:ellipsis;white-space:nowrap}.session-row>view:first-child text{margin-top:6rpx;color:#7e8a98;font-size:19rpx}.session-side{text-align:right}.session-side strong{color:#22685f;font-size:21rpx}.session-side text,.session-side small{margin-top:4rpx;color:#85909c;font-size:18rpx}.onu-button{display:flex;align-items:center;justify-content:center;height:82rpx;margin-top:22rpx;border-radius:14rpx;background:#246e79;color:#fff;font-size:25rpx;font-weight:650}
</style>
