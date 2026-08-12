<template>
  <view class="page installation-page">
    <view class="header"><view class="header-title">五项智能检测</view><view class="header-desc">照片仅归属当前智维工单，检测标准由 Web 管理端统一配置</view></view>
    <view v-if="loading" class="state">正在加载检测记录…</view>
    <template v-else>
      <view v-for="agent in agents" :key="agent.code" class="agent-card">
        <view class="agent-head"><view><view class="agent-name">{{ agent.name }}</view><view class="agent-hint">{{ agent.hint }}</view></view><text :class="['badge', resultFor(agent.code).state]">{{ resultFor(agent.code).label }}</text></view>
        <image v-if="photoFor(agent.code)" class="evidence" :src="assetUrl(photoFor(agent.code).download_url)" mode="aspectFill" />
        <view v-if="resultFor(agent.code).score !== null" class="result-row"><text>评分 {{ resultFor(agent.code).score }} 分</text><text>{{ resultFor(agent.code).passed ? '通过' : '需整改' }}</text></view>
        <view class="agent-actions"><button class="secondary" :disabled="locked" @tap="choosePhoto(agent)">{{ photoFor(agent.code) ? '重拍照片' : '拍照/选图' }}</button><button class="primary" :loading="running === agent.code" :disabled="locked || !photoFor(agent.code)" @tap="run(agent)">智能检测</button></view>
      </view>
      <view v-if="caseData.status === 'awaiting_signature'" class="signature-card">
        <view class="agent-name">客户签字确认</view><input v-model.trim="signerName" class="signer" placeholder="签字人姓名（选填）" /><button class="primary full" :loading="signing" @tap="chooseSignature">上传签字并完成工单</button>
      </view>
      <view v-if="caseData.status === 'completed'" class="complete-card">
        <view class="complete-title">智能装维已完成</view><view>检测结果和现场照片已进入智维平台历史工单。</view><button v-if="order.source_system === 'OSS'" class="primary full" :loading="returning" @tap="returnToOss">回单至公单通</button>
      </view>
      <button v-if="caseData.status === 'draft'" class="submit" :loading="submitting" @tap="submit">提交五项检测</button>
      <button v-if="caseData.status === 'rejected'" class="submit retry" @tap="restart">整改后重新检测</button>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getBaseUrl } from '../../api/request'
import { getWorkOrder, returnOssOrder, runInstallationAgent, startInstallation, submitInstallation, uploadInstallationPhoto, uploadInstallationSignature } from '../../api/workOrders'

const agents = [
  { code: 'site_environment', name: '安装环境检测', hint: '识别安装位置、施工环境与安全条件' },
  { code: 'onu_label', name: 'ONU 标签检测', hint: '识别设备标签、型号和编码清晰度' },
  { code: 'optical_power', name: '光功率检测', hint: '识别仪表读数并按配置范围评分' },
  { code: 'speed_test', name: '测速结果检测', hint: '识别上下行速率、时延及达标情况' },
  { code: 'splitter_box', name: '分纤箱检测', hint: '识别箱体、端口、走线和标签规范' }
]
const orderId = ref('')
const order = ref({})
const loading = ref(false)
const running = ref('')
const submitting = ref(false)
const signing = ref(false)
const returning = ref(false)
const signerName = ref('')
const caseData = computed(() => order.value.installation || {})
const attempt = computed(() => caseData.value.attempts?.[0] || {})
const locked = computed(() => caseData.value.status !== 'draft')

onLoad((query) => { orderId.value = query.id || '' })
onShow(load)
async function load() {
  if (!orderId.value) return
  loading.value = true
  try { order.value = await getWorkOrder(orderId.value) }
  catch (error) { uni.showToast({ title: error.message || '检测记录加载失败', icon: 'none' }) }
  finally { loading.value = false }
}
function photoFor(code) { return (attempt.value.photos || []).find((photo) => photo.agent_code === code && photo.evidence_status === 'active') }
function latestRun(code) { return (attempt.value.ai_runs || []).find((run) => run.agent_code === code) }
function resultFor(code) {
  const run = latestRun(code)
  if (!run) return { state: 'pending', label: photoFor(code) ? '待检测' : '待拍照', score: null, passed: false }
  if (run.status !== 'success') return { state: 'failed', label: '检测异常', score: run.score, passed: false }
  return { state: run.passed ? 'passed' : 'failed', label: run.passed ? '已通过' : '未通过', score: run.score, passed: run.passed }
}
function assetUrl(path) { return path ? `${getBaseUrl().replace(/\/api\/netops2026$/, '')}${path}` : '' }
function choosePhoto(agent) {
  uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['camera', 'album'], success: async (result) => {
    try { uni.showLoading({ title: '正在上传' }); await uploadInstallationPhoto(orderId.value, agent.code, result.tempFilePaths[0]); await load(); uni.showToast({ title: '照片已上传', icon: 'success' }) }
    catch (error) { uni.showToast({ title: error.message || '照片上传失败', icon: 'none' }) }
    finally { uni.hideLoading() }
  } })
}
async function run(agent) {
  if (running.value) return
  running.value = agent.code
  try { await runInstallationAgent(orderId.value, agent.code); await load() }
  catch (error) { uni.showToast({ title: error.message || '智能检测失败', icon: 'none' }) }
  finally { running.value = '' }
}
async function submit() {
  if (submitting.value) return
  submitting.value = true
  try { const result = await submitInstallation(orderId.value); await load(); uni.showModal({ title: result.passed ? '检测通过' : '需要整改', content: result.passed ? '请上传客户签字完成本次装维。' : '请根据检测结果整改后重新检测。', showCancel: false }) }
  catch (error) { uni.showToast({ title: error.message || '请先完成全部五项检测', icon: 'none' }) }
  finally { submitting.value = false }
}
async function restart() {
  try { await startInstallation(orderId.value); await load() }
  catch (error) { uni.showToast({ title: error.message || '无法开始新一轮检测', icon: 'none' }) }
}
function chooseSignature() {
  uni.chooseImage({ count: 1, sizeType: ['compressed'], sourceType: ['camera', 'album'], success: async (result) => {
    signing.value = true
    try { await uploadInstallationSignature(orderId.value, result.tempFilePaths[0], signerName.value); await load(); uni.showToast({ title: '工单已完成', icon: 'success' }) }
    catch (error) { uni.showToast({ title: error.message || '签字上传失败', icon: 'none' }) }
    finally { signing.value = false }
  } })
}
async function returnToOss() {
  returning.value = true
  try { await returnOssOrder(orderId.value, { result: 'completed' }); uni.showToast({ title: '已提交公单通回单', icon: 'success' }) }
  catch (error) { uni.showToast({ title: error.message || '公单通回单失败', icon: 'none' }) }
  finally { returning.value = false }
}
</script>

<style scoped>
.installation-page{padding-bottom:130rpx}.header{margin:-24rpx -24rpx 22rpx;padding:34rpx 28rpx;background:linear-gradient(145deg,#203147,#2b618f);color:#fff}.header-title{font-size:35rpx;font-weight:700}.header-desc{margin-top:10rpx;color:rgba(255,255,255,.7);font-size:22rpx}.state{padding:90rpx 0;color:#7b8794;text-align:center}.agent-card,.signature-card,.complete-card{margin-top:18rpx;padding:24rpx;border:1rpx solid #e1e8ef;border-radius:18rpx;background:#fff}.agent-head{display:flex;justify-content:space-between;gap:20rpx}.agent-name{color:#1c2939;font-size:28rpx;font-weight:700}.agent-hint{margin-top:6rpx;color:#7a8796;font-size:22rpx}.badge{flex:none;align-self:flex-start;padding:6rpx 13rpx;border-radius:18rpx;font-size:21rpx}.badge.pending{background:#eef2f6;color:#637083}.badge.passed{background:#e3f4ec;color:#15704f}.badge.failed{background:#fff0eb;color:#b04b2e}.evidence{width:100%;height:300rpx;margin-top:18rpx;border-radius:14rpx;background:#edf1f5}.result-row{display:flex;justify-content:space-between;margin-top:14rpx;color:#536174;font-size:23rpx}.agent-actions{display:flex;gap:14rpx;margin-top:18rpx}.agent-actions button{flex:1;min-height:72rpx;border-radius:12rpx;font-size:24rpx}.primary,.submit{background:#2269c8;color:#fff}.secondary{border:1rpx solid #cbd6e1;background:#fff;color:#37516d}.submit{position:sticky;bottom:22rpx;width:100%;margin-top:24rpx;min-height:86rpx;border-radius:15rpx;font-size:27rpx;box-shadow:0 8rpx 22rpx rgba(30,72,124,.2)}.retry{background:#a55c19}.signer{height:76rpx;margin:18rpx 0;padding:0 18rpx;border-radius:12rpx;background:#f2f5f8;font-size:25rpx}.full{width:100%;margin-top:18rpx;border-radius:13rpx}.complete-card{color:#637083;font-size:23rpx}.complete-title{margin-bottom:9rpx;color:#177052;font-size:29rpx;font-weight:700}
</style>
