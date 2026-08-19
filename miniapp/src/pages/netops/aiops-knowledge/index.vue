<template>
  <view class="netops-page kb-page">
    <view class="kb-hero"><view><text>AIOPS KNOWLEDGE</text><strong>故障知识库</strong><small>故障报告、值班经验与运维文档统一检索</small></view><view class="hero-icon">库</view></view>
    <view class="metric-grid"><view><strong>{{ summary.formal_report_count || 0 }}</strong><text>正式报告</text></view><view><strong>{{ summary.repair_count || 0 }}</strong><text>值班经验</text></view><view><strong>{{ summary.document_count || 0 }}</strong><text>运维文档</text></view><view><strong>{{ summary.topic_count || 0 }}</strong><text>故障主题</text></view></view>
    <scroll-view scroll-x class="tab-scroll" :show-scrollbar="false"><view class="tabs"><view v-for="item in tabs" :key="item.value" class="tab" :class="{ active: type === item.value }" @tap="switchType(item.value)">{{ item.label }}</view></view></scroll-view>
    <view class="search-bar"><input v-model.trim="keyword" class="search-input" placeholder="搜索现象、原因、处置方法或文件" confirm-type="search" @confirm="reload" /><button class="search-button" @tap="reload">查询</button></view>
    <view v-if="error" class="notice">{{ error }}</view>
    <view class="section-card result-card"><view class="section-head"><view class="section-head-title">{{ currentLabel }}</view><view class="section-head-meta">{{ total }} 条</view></view>
      <view v-if="items.length" class="knowledge-list"><view v-for="(item,index) in items" :key="item.record_id || item.aggregate_id || index" class="knowledge-item" @tap="selected = item"><view class="knowledge-top"><text>{{ service(item) }}</text><text>{{ dateText(item) }}</text></view><view class="knowledge-title">{{ title(item) }}</view><view class="knowledge-summary">{{ summaryText(item) }}</view><view class="knowledge-foot"><text>{{ sourceText(item) }}</text><text>查看详情 ›</text></view></view></view>
      <view v-else-if="loading" class="status-text">正在检索知识库…</view><EmptyState v-else mark="库" title="没有匹配的知识条目" description="可尝试更换关键词或分类。" />
      <view v-if="items.length < total" class="load-more" @tap="loadMore">{{ loading ? '加载中…' : '继续加载' }}</view>
    </view>
    <view v-if="selected" class="mask" @tap="selected = null"><view class="detail-sheet" @tap.stop><view class="sheet-head"><view><text>{{ currentLabel }}</text><strong>{{ title(selected) }}</strong></view><view @tap="selected = null">×</view></view><scroll-view scroll-y class="detail-scroll"><view v-for="entry in detailEntries" :key="entry.key" class="detail-row"><text>{{ entry.key }}</text><view>{{ entry.value }}</view></view></scroll-view></view></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import { getKnowledgeItems, getKnowledgeSummary } from '../../../api/aiops'
import { messageLabel } from '../../../utils/labels'

const tabs = [{ label: '正式报告', value: 'reports' }, { label: '值班经验', value: 'repairs' }, { label: '运维文档', value: 'documents' }, { label: '故障主题', value: 'topics' }]
const type = ref('reports'); const keyword = ref(''); const summary = ref({}); const items = ref([]); const total = ref(0); const offset = ref(0); const loading = ref(false); const error = ref(''); const selected = ref(null); const pageSize = 15
const currentLabel = computed(() => (tabs.find((item) => item.value === type.value) || tabs[0]).label)
const detailEntries = computed(() => Object.entries(selected.value || {}).filter(([, value]) => value !== null && value !== '' && (!Array.isArray(value) || value.length)).map(([key, value]) => ({ key: fieldLabel(key), value: text(value) })))
onLoad(() => { loadSummary(); reload() })
async function loadSummary() { try { summary.value = await getKnowledgeSummary() } catch (_) {} }
function switchType(value) { type.value = value; keyword.value = ''; reload() }
function reload() { offset.value = 0; items.value = []; load() }
function loadMore() { if (!loading.value && items.value.length < total.value) { offset.value = items.value.length; load(true) } }
async function load(append = false) { loading.value = true; error.value = ''; try { const data = await getKnowledgeItems(type.value, { q: keyword.value, limit: pageSize, offset: offset.value }); items.value = append ? items.value.concat(data.items || []) : (data.items || []); total.value = Number(data.total || 0) } catch (err) { error.value = messageLabel(err.message) } finally { loading.value = false } }
function text(value, fallback = '--') { if (Array.isArray(value)) return value.filter(Boolean).map((item) => typeof item === 'object' ? JSON.stringify(item) : item).join('；') || fallback; if (value && typeof value === 'object') return JSON.stringify(value, null, 2); return String(value || '').trim() || fallback }
function title(item) { return text(item.knowledge_title || item.title || item.topic_label || item.canonical_symptom_label || item.fault_content, '未命名知识条目') }
function service(item) { return text(item.service || item.business_type, '综合运维') }
function dateText(item) { return text(item.occurred_date || item.last_seen || item.updated_at, '').slice(0, 10) }
function summaryText(item) { const value = text(item.root_cause || item.knowledge_content || item.fault_content || item.handling_result || item.fix_method || item.canonical_symptom, '暂无摘要'); return value.length > 120 ? `${value.slice(0, 120)}…` : value }
function sourceText(item) { return text(item.report_file || item.source_file || item.topic_source, '知识库') }
function fieldLabel(key) { return ({ service: '业务系统', occurred_date: '发生日期', fault_content: '故障内容', root_cause: '故障原因', handling_result: '处理结果', fix_method: '处置方法', investigation_steps: '排查步骤', source_file: '来源文件', report_file: '报告文件', canonical_symptom: '故障症状', knowledge_content: '知识内容' })[key] || key }
</script>

<style scoped>
.kb-page{padding-top:0}.kb-hero{display:flex;align-items:center;justify-content:space-between;margin:0 -24rpx 18rpx;padding:34rpx 30rpx;border-radius:0 0 28rpx 28rpx;background:linear-gradient(145deg,#292450,#5548a4);color:#fff}.kb-hero text,.kb-hero strong,.kb-hero small{display:block}.kb-hero text{color:rgba(255,255,255,.52);font-size:17rpx;letter-spacing:2rpx}.kb-hero strong{margin-top:7rpx;font-size:33rpx}.kb-hero small{margin-top:7rpx;color:rgba(255,255,255,.68);font-size:19rpx}.hero-icon{display:flex;width:68rpx;height:68rpx;align-items:center;justify-content:center;border:1rpx solid rgba(255,255,255,.25);border-radius:22rpx;background:rgba(255,255,255,.11);font-size:25rpx}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);margin-bottom:17rpx;padding:17rpx 6rpx;border:1rpx solid #e1e7ee;border-radius:17rpx;background:#fff}.metric-grid view{text-align:center}.metric-grid strong,.metric-grid text{display:block}.metric-grid strong{color:#342d70;font-size:25rpx}.metric-grid text{margin-top:4rpx;color:#8a94a1;font-size:16rpx}.tab-scroll{width:100%;margin-bottom:15rpx;white-space:nowrap}.tabs{display:inline-flex;gap:10rpx}.tab{padding:13rpx 19rpx;border:1rpx solid #dfe5ec;border-radius:99rpx;background:#fff;color:#687588;font-size:20rpx}.tab.active{border-color:#6356aa;background:#6356aa;color:#fff}.notice{margin:14rpx 0;padding:15rpx 18rpx;border-radius:12rpx;background:#fdebea;color:#b34540;font-size:21rpx}.result-card{margin-top:17rpx}.knowledge-list{padding:0 22rpx}.knowledge-item{padding:21rpx 0;border-bottom:1rpx solid #edf1f5}.knowledge-item:last-child{border:0}.knowledge-top,.knowledge-foot{display:flex;justify-content:space-between;gap:16rpx;color:#8a95a2;font-size:18rpx}.knowledge-top text:first-child{color:#6559a8}.knowledge-title{margin-top:9rpx;color:#29394c;font-size:25rpx;font-weight:700;line-height:1.4}.knowledge-summary{margin-top:9rpx;color:#5d6b7d;font-size:21rpx;line-height:1.55}.knowledge-foot{margin-top:11rpx}.knowledge-foot text:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.knowledge-foot text:last-child{flex:none;color:#675aa8}.mask{position:fixed;z-index:60;inset:0;display:flex;align-items:flex-end;background:rgba(20,25,38,.52)}.detail-sheet{width:100%;height:78vh;border-radius:27rpx 27rpx 0 0;background:#f4f6f9}.sheet-head{display:flex;align-items:flex-start;justify-content:space-between;padding:25rpx;border-bottom:1rpx solid #e2e7ed;border-radius:27rpx 27rpx 0 0;background:#fff}.sheet-head text,.sheet-head strong{display:block}.sheet-head text{color:#675aa8;font-size:18rpx}.sheet-head strong{margin-top:6rpx;color:#29394b;font-size:26rpx;line-height:1.4}.sheet-head>view:last-child{padding:0 8rpx;color:#7d8895;font-size:42rpx}.detail-scroll{height:calc(78vh - 122rpx);padding:19rpx 22rpx 40rpx;box-sizing:border-box}.detail-row{margin-bottom:13rpx;padding:18rpx;border:1rpx solid #e2e7ed;border-radius:14rpx;background:#fff}.detail-row>text{display:block;margin-bottom:7rpx;color:#766bb0;font-size:18rpx}.detail-row>view{color:#47576a;font-size:21rpx;line-height:1.6;white-space:pre-wrap}
</style>
