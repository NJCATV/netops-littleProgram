<template>
  <view class="netops-page aiops-page">
    <view class="hero">
      <view><view class="hero-kicker">AI NETWORK OPERATIONS</view><view class="hero-title">AIOps 运维看板</view><view class="hero-sub">查看最新 AI 研判、关键证据与处置建议</view></view>
      <view class="assistant-entry" @tap="openAssistant">问 AI</view>
    </view>

    <view v-if="error" class="error-box">{{ error }}</view>
    <view v-if="loading && !selected" class="section-card"><view class="status-text">正在读取最新 AIOps 分析报告...</view></view>
    <EmptyState v-else-if="!selected" mark="智" title="暂无分析报告" description="Web 端生成分析报告后，小程序会在这里展示最新结论。" />

    <template v-else>
      <scroll-view scroll-x class="run-scroll">
        <view class="run-list">
          <view v-for="run in successfulRuns" :key="run.run_uid" class="run-item" :class="{ active: run.run_uid === selected.run_uid }" @tap="selectRun(run)">
            <strong>{{ shortTime(run.created_at) }}</strong><text>{{ run.hours || 24 }} 小时</text>
          </view>
        </view>
      </scroll-view>

      <view class="status-card" :class="statusTone">
        <view class="status-row"><text>{{ statusLevel }}</text><text>{{ formatTime(selected.created_at) }}</text></view>
        <view class="status-title">{{ status.title || selected.overall_title || '最新 AI 分析结论' }}</view>
        <view class="status-summary">{{ status.summary || selected.summary_text || '当前报告暂无摘要。' }}</view>
        <view class="status-conclusion">{{ status.ai_conclusion || status.conclusion || '请结合下方证据和建议核实。' }}</view>
      </view>

      <view class="source-strip">
        <view><text>Syslog</text><strong>{{ sourceWindow?.syslog_parsed || 0 }}</strong></view>
        <view><text>Trap</text><strong>{{ sourceWindow?.trap_raw || 0 }}</strong></view>
        <view><text>Events</text><strong>{{ sourceWindow?.alarm_events || 0 }}</strong></view>
        <view><text>数据</text><strong :class="{ late: !freshness.is_fresh }">{{ freshness.is_fresh ? '实时' : '延迟' }}</strong></view>
      </view>

      <scroll-view scroll-x class="tab-scroll">
        <view class="tabs">
          <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeSection === tab.key }" @tap="activeSection = tab.key">
            {{ tab.label }} <text>{{ tab.count }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="section-card finding-card">
        <view class="section-head"><view class="section-head-title">{{ activeTabLabel }}</view><view class="section-head-meta">{{ activeFindings.length }} 项</view></view>
        <view v-if="activeFindings.length" class="finding-list">
          <view v-for="(item, index) in activeFindings" :key="item.id || item.finding_uid || index" class="finding" :class="severity(item)" @tap="openFinding(item)">
            <view class="finding-head"><strong>{{ findingTitle(item) }}</strong><text>{{ severityLabel(item) }}</text></view>
            <view class="finding-device">{{ findingDevice(item) }} · {{ text(item.object_key, '设备级') }}</view>
            <view class="finding-summary">{{ findingSummary(item) }}</view>
            <view class="finding-evidence">证据：{{ firstEvidence(item) }}</view>
            <view class="finding-more">查看证据与建议 ›</view>
          </view>
        </view>
        <EmptyState v-else mark="安" title="当前分类暂无分析项" description="可切换其他分类或选择历史分析报告。" />
      </view>

      <view class="section-card report-info">
        <view class="section-head"><view class="section-head-title">报告信息</view><view class="section-head-meta">{{ selected.status || '--' }}</view></view>
        <view class="info-list">
          <view><text>分析窗口</text><strong>{{ formatTime(selected.window_start) }} 至 {{ formatTime(selected.window_end) }}</strong></view>
          <view><text>分析模型</text><strong>{{ modelName }}</strong></view>
          <view><text>执行耗时</text><strong>{{ selected.duration_ms ? `${Math.round(selected.duration_ms / 1000)} 秒` : '--' }}</strong></view>
          <view><text>数据更新</text><strong>{{ formatTime(freshness.latest_alarm_event_at) }}</strong></view>
        </view>
      </view>
    </template>

    <view v-if="selectedFinding" class="overlay" @tap="selectedFinding = null">
      <view class="detail-sheet" @tap.stop>
        <view class="sheet-head"><view><text>{{ severityLabel(selectedFinding) }}</text><strong>{{ findingTitle(selectedFinding) }}</strong></view><view class="close" @tap="selectedFinding = null">×</view></view>
        <scroll-view scroll-y class="sheet-scroll">
          <view class="detail-block"><text>AI 研判</text><view>{{ findingSummary(selectedFinding) }}</view></view>
          <view class="detail-block"><text>关键证据</text><view class="pre">{{ detailText(evidenceValue(selectedFinding)) }}</view></view>
          <view class="detail-block"><text>建议动作</text><view class="pre">{{ detailText(actionValue(selectedFinding)) }}</view></view>
          <view class="detail-block"><text>待补充数据</text><view class="pre">{{ detailText(missingValue(selectedFinding)) }}</view></view>
          <button class="copy-button" @tap="copySuggestion(selectedFinding)">复制处置建议</button>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import { getAiopsFreshness, getAiopsOverview, getAiopsRun, getAiopsRuns } from '../../../api/aiops'
import { messageLabel } from '../../../utils/labels'

const runs = ref([])
const selected = ref(null)
const overview = ref(null)
const freshness = ref({})
const loading = ref(false)
const error = ref('')
const activeSection = ref('must_handle')
const selectedFinding = ref(null)

const successfulRuns = computed(() => runs.value.filter((run) => run.status === 'success'))
const status = computed(() => selected.value?.overall_status || {})
const statusLevel = computed(() => String(status.value.level || selected.value?.overall_level || 'stable').toUpperCase())
const statusTone = computed(() => {
  const value = statusLevel.value.toLowerCase()
  return /critical|high|danger|严重/.test(value) ? 'danger' : /warning|medium|watch|关注/.test(value) ? 'warn' : 'stable'
})
const sections = computed(() => ({
  must_handle: selected.value?.must_handle || [],
  watch: selected.value?.watch || [],
  correlations: selected.value?.correlations || [],
  recovered: selected.value?.recovered || [],
  next_actions: selected.value?.next_actions || [],
  noise: selected.value?.noise || [],
  insufficient: selected.value?.insufficient || []
}))
const tabs = computed(() => [
  { key: 'must_handle', label: '必须处理', count: sections.value.must_handle.length },
  { key: 'watch', label: '重点关注', count: sections.value.watch.length },
  { key: 'correlations', label: '关联分析', count: sections.value.correlations.length },
  { key: 'recovered', label: '已恢复', count: sections.value.recovered.length },
  { key: 'next_actions', label: '建议动作', count: sections.value.next_actions.length },
  { key: 'noise', label: '降噪', count: sections.value.noise.length },
  { key: 'insufficient', label: '证据不足', count: sections.value.insufficient.length }
])
const activeFindings = computed(() => sections.value[activeSection.value] || [])
const activeTabLabel = computed(() => tabs.value.find((tab) => tab.key === activeSection.value)?.label || '分析项')
const sourceWindow = computed(() => overview.value?.windows?.find((item) => Number(item.hours) === Number(selected.value?.hours || 24)) || overview.value?.windows?.find((item) => Number(item.hours) === 24))
const modelName = computed(() => selected.value?.model_trace || [selected.value?.llm_provider, selected.value?.model_name].filter(Boolean).join(' / ') || '--')

onLoad(() => load())
onPullDownRefresh(() => load(true))

async function load(fromPull = false) {
  loading.value = true
  error.value = ''
  try {
    const [runData, overviewData, freshnessData] = await Promise.all([getAiopsRuns(30), getAiopsOverview(24), getAiopsFreshness()])
    runs.value = runData.items || []
    overview.value = overviewData
    freshness.value = freshnessData || {}
    const target = successfulRuns.value[0] || runs.value[0]
    if (target) await selectRun(target)
  } catch (err) {
    error.value = messageLabel(err.message)
  } finally {
    loading.value = false
    if (fromPull) uni.stopPullDownRefresh()
  }
}

async function selectRun(run) {
  if (!run?.run_uid) return
  try {
    const data = await getAiopsRun(run.run_uid)
    selected.value = data.item || run
    activeSection.value = 'must_handle'
  } catch (err) {
    error.value = messageLabel(err.message)
  }
}

function text(value, fallback = '--') {
  if (value === 0) return '0'
  if (Array.isArray(value)) return value.length ? value.map((item) => text(item, '')).join('、') : fallback
  if (value && typeof value === 'object') return value.title || value.summary || value.action || JSON.stringify(value)
  return value || fallback
}
function short(value, max = 150) { const content = text(value, ''); return content.length > max ? `${content.slice(0, max)}…` : content }
function severity(item) { return String(item.severity || item.level || item.priority || 'info').toLowerCase() }
function severityLabel(item) {
  const value = severity(item)
  if (/critical|high|danger/.test(value)) return '高风险'
  if (/warning|medium|watch/.test(value)) return '需关注'
  if (/ok|stable|recovered|low/.test(value)) return '稳定'
  return '提示'
}
function findingTitle(item) { return item.title || item.action || item.reason || item.conclusion || 'AI 分析项' }
function findingSummary(item) { return item.root_cause_hypothesis || item.judgment || item.conclusion || item.summary || item.reason || item.impact || item.action || '暂无摘要' }
function findingDevice(item) { return item.managed_device_name || item.device_name || item.managed_device_ip || item.device_ip || (item.devices || []).join('、') || '多对象关联' }
function firstEvidence(item) {
  const evidence = item.evidence || item.raw?.evidence || []
  return short(Array.isArray(evidence) ? evidence[0] : evidence, 120) || '证据随报告原文保存'
}
function detailText(value, fallback = '暂无结构化内容') {
  if (!value) return fallback
  if (Array.isArray(value)) return value.length ? value.map((item, index) => `${index + 1}. ${text(item)}`).join('\n') : fallback
  if (typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}：${text(item)}`).join('\n')
  return String(value)
}
function actionValue(item) { return item.recommended_actions || item.action || item.next_action || item.suggestion || item.raw?.recommended_actions }
function evidenceValue(item) { return item.evidence || item.related_events || item.raw?.evidence }
function missingValue(item) { return item.missing_data || item.missing || item.raw?.missing_data }
function openFinding(item) { selectedFinding.value = item }
function copySuggestion(item) {
  uni.setClipboardData({ data: detailText(actionValue(item)), success: () => uni.showToast({ title: '建议已复制', icon: 'success' }) })
}
function openAssistant() { uni.switchTab({ url: '/pages/netops/ai-assistant/index' }) }
function formatTime(value) {
  if (!value) return '--'
  const date = new Date(String(value))
  if (Number.isNaN(date.getTime())) return String(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
function shortTime(value) { const textValue = formatTime(value); return textValue === '--' ? '--' : textValue.slice(5) }
</script>

<style scoped>
.aiops-page{padding-top:0}.hero{display:flex;align-items:center;justify-content:space-between;gap:18rpx;margin:0 -24rpx 22rpx;padding:40rpx 30rpx 36rpx;border-radius:0 0 30rpx 30rpx;background:linear-gradient(145deg,#29264f,#514c93);color:#fff}.hero-kicker{color:rgba(255,255,255,.55);font-size:18rpx;letter-spacing:2rpx}.hero-title{margin-top:8rpx;font-size:36rpx;font-weight:750}.hero-sub{margin-top:8rpx;color:rgba(255,255,255,.68);font-size:21rpx}.assistant-entry{flex:none;padding:13rpx 18rpx;border:1rpx solid rgba(255,255,255,.25);border-radius:99rpx;font-size:22rpx}.error-box{margin-bottom:18rpx;padding:18rpx 20rpx;border-radius:12rpx;background:#fdeceb;color:#b63f39;font-size:23rpx}.run-scroll,.tab-scroll{width:100%;white-space:nowrap}.run-list,.tabs{display:inline-flex;gap:12rpx;padding-bottom:16rpx}.run-item{display:flex;min-width:126rpx;padding:13rpx 16rpx;border:1rpx solid #dde4ec;border-radius:13rpx;background:#fff;flex-direction:column}.run-item strong{color:#425267;font-size:21rpx}.run-item text{margin-top:4rpx;color:#8994a1;font-size:17rpx}.run-item.active{border-color:#6960b5;background:#eeecfa}.run-item.active strong{color:#51489b}.status-card{padding:26rpx;border:1rpx solid #dfe5ed;border-left:8rpx solid #3f836e;border-radius:18rpx;background:#fff}.status-card.warn{border-left-color:#c88126}.status-card.danger{border-left-color:#c34a44}.status-row{display:flex;justify-content:space-between;color:#758293;font-size:19rpx}.status-title{margin-top:13rpx;color:#26364a;font-size:31rpx;font-weight:750;line-height:1.35}.status-summary{margin-top:12rpx;color:#536277;font-size:23rpx;line-height:1.6}.status-conclusion{margin-top:16rpx;padding:15rpx 17rpx;border-radius:10rpx;background:#f3f2fb;color:#504989;font-size:21rpx;line-height:1.5}.source-strip{display:grid;grid-template-columns:repeat(4,1fr);margin:18rpx 0;padding:18rpx 8rpx;border:1rpx solid #e1e7ee;border-radius:15rpx;background:#fff}.source-strip view{text-align:center}.source-strip text,.source-strip strong{display:block}.source-strip text{color:#8994a1;font-size:18rpx}.source-strip strong{margin-top:5rpx;color:#37485c;font-size:22rpx}.source-strip strong.late{color:#b76a1e}.tab{padding:14rpx 18rpx;border:1rpx solid #dfe5ec;border-radius:99rpx;background:#fff;color:#5f6d7e;font-size:21rpx}.tab text{margin-left:5rpx;color:#8b95a2}.tab.active{border-color:#655bab;background:#655bab;color:#fff}.tab.active text{color:rgba(255,255,255,.72)}.finding-card{margin-top:0}.finding-list{padding:0 22rpx}.finding{position:relative;padding:22rpx 0;border-bottom:1rpx solid #edf1f5}.finding:last-child{border-bottom:0}.finding-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18rpx}.finding-head strong{color:#2c3d50;font-size:25rpx;line-height:1.4}.finding-head text{flex:none;padding:5rpx 10rpx;border-radius:99rpx;background:#edf1f5;color:#637184;font-size:17rpx}.finding.high .finding-head text,.finding.critical .finding-head text,.finding.danger .finding-head text{background:#fdebea;color:#b7403a}.finding.warning .finding-head text,.finding.medium .finding-head text,.finding.watch .finding-head text{background:#fff1dc;color:#a86715}.finding-device{margin-top:7rpx;color:#8994a1;font-size:19rpx}.finding-summary{margin-top:12rpx;color:#4b5a6d;font-size:22rpx;line-height:1.58}.finding-evidence{margin-top:10rpx;padding:12rpx 14rpx;border-radius:9rpx;background:#f5f7fa;color:#6e7b8b;font-size:19rpx;line-height:1.5}.finding-more{margin-top:11rpx;color:#665da5;font-size:19rpx;text-align:right}.report-info{margin-top:20rpx}.info-list{padding:4rpx 24rpx 17rpx}.info-list view{display:flex;justify-content:space-between;gap:18rpx;padding:15rpx 0;border-bottom:1rpx solid #edf1f5}.info-list view:last-child{border-bottom:0}.info-list text{flex:none;color:#8994a1;font-size:20rpx}.info-list strong{color:#435166;font-size:20rpx;font-weight:500;text-align:right}.overlay{position:fixed;z-index:40;inset:0;display:flex;align-items:flex-end;background:rgba(20,25,38,.52)}.detail-sheet{width:100%;height:78vh;border-radius:28rpx 28rpx 0 0;background:#f4f6f9}.sheet-head{display:flex;align-items:flex-start;justify-content:space-between;padding:26rpx;border-bottom:1rpx solid #e1e6ed;background:#fff;border-radius:28rpx 28rpx 0 0}.sheet-head>view:first-child{min-width:0}.sheet-head text,.sheet-head strong{display:block}.sheet-head text{color:#756cae;font-size:19rpx}.sheet-head strong{margin-top:7rpx;color:#28384b;font-size:28rpx;line-height:1.4}.close{padding:0 8rpx;color:#7c8795;font-size:44rpx}.sheet-scroll{height:calc(78vh - 112rpx);padding:22rpx 24rpx 42rpx;box-sizing:border-box}.detail-block{margin-bottom:18rpx;padding:20rpx;border:1rpx solid #e1e6ed;border-radius:15rpx;background:#fff}.detail-block>text{display:block;margin-bottom:9rpx;color:#756cae;font-size:19rpx;font-weight:700}.detail-block>view{color:#4c5b6d;font-size:22rpx;line-height:1.6;white-space:pre-wrap}.copy-button{display:flex;align-items:center;justify-content:center;height:78rpx;border-radius:13rpx;background:#6258a7;color:#fff;font-size:24rpx}
</style>
