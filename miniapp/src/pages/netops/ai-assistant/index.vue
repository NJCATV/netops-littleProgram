<template>
  <view class="assistant-page">
    <view class="assistant-head">
      <view class="avatar">AI</view>
      <view class="head-copy"><strong>AI 运维助手</strong><text>故障知识、值班经验与 AIOps 数据统一问答</text></view>
      <view class="history-button" @tap="showHistory = !showHistory">{{ showHistory ? '返回' : '历史' }}</view>
    </view>

    <view v-if="showHistory" class="history-panel">
      <view class="history-title"><strong>历史对话</strong><view @tap="newChat">＋ 新对话</view></view>
      <view v-if="sessions.length" class="session-list">
        <view v-for="session in sessions" :key="session.id" class="session-row" :class="{ active: currentSessionId === session.id }">
          <view class="session-main" @tap="openSession(session.id)"><strong>{{ session.title || '未命名对话' }}</strong><text>{{ formatTime(session.last_message_at) }} · {{ session.message_count || 0 }} 条</text></view>
          <view class="delete" @tap="confirmDelete(session)">删</view>
        </view>
      </view>
      <EmptyState v-else mark="问" title="暂无历史对话" description="发送第一条问题后会自动创建会话。" />
    </view>

    <template v-else>
      <scroll-view scroll-y class="messages" :scroll-into-view="scrollTarget" scroll-with-animation>
        <view v-if="!messages.length" class="welcome">
          <view class="welcome-mark">AI</view>
          <strong>今天需要排查什么问题？</strong>
          <text>可以描述用户现象、设备告警或业务影响，助手会按需检索故障知识和 AIOps 数据。</text>
          <view class="suggestions">
            <view v-for="item in suggestions" :key="item" @tap="useSuggestion(item)">{{ item }}</view>
          </view>
        </view>

        <view v-for="(message, index) in messages" :id="`message-${index}`" :key="message.id || index" class="message" :class="message.role">
          <view class="message-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</view>
          <view class="bubble"><text>{{ message.content }}</text><small v-if="message.created_at">{{ formatTime(message.created_at) }}</small><small v-if="message.model_error" class="message-error">模型调用异常：{{ message.model_error }}</small></view>
        </view>
        <view v-if="sending" id="message-sending" class="message assistant">
          <view class="message-avatar">AI</view>
          <view class="bubble thinking"><text>正在分析问题和相关知识...</text></view>
        </view>
        <view class="bottom-space" />
      </scroll-view>

      <view v-if="error" class="error-bar">{{ error }}</view>
      <view class="composer">
        <textarea v-model="input" class="composer-input" auto-height :maxlength="2000" placeholder="输入运维问题..." confirm-type="send" />
        <view class="composer-foot"><text>AI 结论请结合原始证据核实</text><button :disabled="sending || !input.trim()" @tap="send">发送</button></view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import EmptyState from '../../../components/netops/EmptyState.vue'
import { deleteAiChatSession, getAiChatSession, getAiChatSessions, sendAiChatMessage } from '../../../api/aiops'
import { messageLabel } from '../../../utils/labels'
import { syncCustomTabBar } from '../../../utils/tab-bar'

const sessions = ref([])
const messages = ref([])
const currentSessionId = ref(null)
const input = ref('')
const sending = ref(false)
const error = ref('')
const showHistory = ref(false)
const scrollTarget = ref('')
const suggestions = ['用户反馈点播卡顿，应该按什么顺序排查？', '宽带测速不达标有哪些常见原因？', '帮我总结最近的高风险告警']

onLoad(loadSessions)
onShow(() => syncCustomTabBar(1))

async function loadSessions() {
  try {
    const data = await getAiChatSessions(30)
    sessions.value = data.items || []
  } catch (err) {
    error.value = messageLabel(err.message)
  }
}

async function openSession(id) {
  error.value = ''
  try {
    const data = await getAiChatSession(id)
    currentSessionId.value = data.session.id
    messages.value = data.messages || []
    showHistory.value = false
    scrollBottom()
  } catch (err) {
    error.value = messageLabel(err.message)
  }
}

function newChat() {
  currentSessionId.value = null
  messages.value = []
  input.value = ''
  error.value = ''
  showHistory.value = false
}

function confirmDelete(session) {
  uni.showModal({
    title: '删除对话',
    content: `确认删除“${session.title || '未命名对话'}”？`,
    success: async (result) => {
      if (!result.confirm) return
      try {
        await deleteAiChatSession(session.id)
        if (currentSessionId.value === session.id) newChat()
        await loadSessions()
      } catch (err) {
        uni.showToast({ title: messageLabel(err.message), icon: 'none' })
      }
    }
  })
}

async function send() {
  const content = input.value.trim()
  if (!content || sending.value) return
  messages.value.push({ role: 'user', content, created_at: new Date().toISOString() })
  input.value = ''
  sending.value = true
  error.value = ''
  scrollBottom(true)
  try {
    const result = await sendAiChatMessage(content, currentSessionId.value)
    currentSessionId.value = result.session_id || currentSessionId.value
    messages.value.push({
      role: 'assistant',
      content: result.answer || '暂时没有生成回答。',
      evidence: result.evidence,
      model_error: result.model_error,
      created_at: result.created_at
    })
    await loadSessions()
  } catch (err) {
    const message = messageLabel(err.message)
    error.value = message
    messages.value.push({ role: 'assistant', content: `本次问答失败：${message}` })
  } finally {
    sending.value = false
    scrollBottom()
  }
}

function useSuggestion(value) { input.value = value }
async function scrollBottom(thinking = false) {
  await nextTick()
  scrollTarget.value = ''
  await nextTick()
  scrollTarget.value = thinking ? 'message-sending' : `message-${Math.max(0, messages.value.length - 1)}`
}
function formatTime(value) {
  if (!value) return ''
  const date = new Date(String(value))
  if (Number.isNaN(date.getTime())) return String(value)
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.assistant-page{height:100vh;overflow:hidden;background:#f3f5f8}.assistant-head{display:flex;height:112rpx;align-items:center;gap:16rpx;padding:0 24rpx;border-bottom:1rpx solid #dfe5ec;background:linear-gradient(135deg,#29264f,#514c93);color:#fff;box-sizing:border-box}.avatar{display:flex;width:58rpx;height:58rpx;flex:none;align-items:center;justify-content:center;border-radius:18rpx;background:rgba(255,255,255,.16);font-size:21rpx;font-weight:750}.head-copy{min-width:0;flex:1}.head-copy strong,.head-copy text{display:block}.head-copy strong{font-size:27rpx}.head-copy text{margin-top:5rpx;overflow:hidden;color:rgba(255,255,255,.65);font-size:18rpx;text-overflow:ellipsis;white-space:nowrap}.history-button{padding:10rpx 15rpx;border:1rpx solid rgba(255,255,255,.25);border-radius:99rpx;font-size:20rpx}.history-panel{height:calc(100vh - 112rpx);padding:22rpx 24rpx 48rpx;overflow-y:auto;box-sizing:border-box}.history-title{display:flex;align-items:center;justify-content:space-between;margin-bottom:16rpx}.history-title strong{color:#2a394b;font-size:28rpx}.history-title view{color:#6259a6;font-size:22rpx}.session-list{overflow:hidden;border:1rpx solid #e0e6ed;border-radius:17rpx;background:#fff}.session-row{display:flex;align-items:center;gap:14rpx;padding:19rpx 20rpx;border-bottom:1rpx solid #edf1f5}.session-row:last-child{border-bottom:0}.session-row.active{background:#f0eefb}.session-main{min-width:0;flex:1}.session-main strong,.session-main text{display:block}.session-main strong{overflow:hidden;color:#344458;font-size:23rpx;text-overflow:ellipsis;white-space:nowrap}.session-main text{margin-top:7rpx;color:#8b96a3;font-size:18rpx}.delete{padding:8rpx;color:#b65650;font-size:19rpx}.messages{height:calc(100vh - 112rpx - 190rpx);padding:22rpx 24rpx 0;box-sizing:border-box}.welcome{padding:58rpx 22rpx;text-align:center}.welcome-mark{display:flex;width:82rpx;height:82rpx;margin:0 auto 20rpx;align-items:center;justify-content:center;border-radius:25rpx;background:#ebe9f8;color:#6158a5;font-size:25rpx;font-weight:750}.welcome strong,.welcome>text{display:block}.welcome strong{color:#2e3e51;font-size:29rpx}.welcome>text{margin-top:11rpx;color:#788493;font-size:21rpx;line-height:1.55}.suggestions{display:flex;margin-top:26rpx;flex-direction:column;gap:12rpx}.suggestions view{padding:17rpx 20rpx;border:1rpx solid #e0e5ed;border-radius:13rpx;background:#fff;color:#5a528f;font-size:21rpx;text-align:left}.message{display:flex;align-items:flex-start;gap:13rpx;margin-bottom:22rpx}.message.user{flex-direction:row-reverse}.message-avatar{display:flex;width:54rpx;height:54rpx;flex:none;align-items:center;justify-content:center;border-radius:17rpx;background:#6259a7;color:#fff;font-size:19rpx;font-weight:700}.message.user .message-avatar{background:#2c6ca8}.bubble{max-width:calc(100% - 86rpx);padding:18rpx 20rpx;border:1rpx solid #e0e5ec;border-radius:6rpx 17rpx 17rpx 17rpx;background:#fff}.message.user .bubble{border-color:#cfe0f0;border-radius:17rpx 6rpx 17rpx 17rpx;background:#e8f2fb}.bubble>text{display:block;color:#344458;font-size:23rpx;line-height:1.65;white-space:pre-wrap}.bubble small{display:block;margin-top:9rpx;color:#98a2ae;font-size:17rpx}.bubble .message-error{color:#b64b45}.thinking{color:#6d659c}.bottom-space{height:20rpx}.error-bar{position:fixed;right:24rpx;bottom:190rpx;left:24rpx;z-index:3;padding:12rpx 16rpx;border-radius:10rpx;background:#fdebea;color:#b5413b;font-size:19rpx}.composer{position:fixed;right:0;bottom:0;left:0;height:190rpx;padding:15rpx 20rpx 18rpx;border-top:1rpx solid #dde4eb;background:#fff;box-sizing:border-box}.composer-input{width:100%;min-height:82rpx;max-height:104rpx;padding:14rpx 17rpx;border:1rpx solid #d8e0e8;border-radius:13rpx;background:#f7f9fb;color:#2f4054;font-size:23rpx;line-height:1.5;box-sizing:border-box}.composer-foot{display:flex;align-items:center;justify-content:space-between;margin-top:10rpx}.composer-foot text{color:#909aa6;font-size:17rpx}.composer-foot button{display:flex;width:104rpx;height:55rpx;align-items:center;justify-content:center;border-radius:11rpx;background:#6259a7;color:#fff;font-size:21rpx}.composer-foot button[disabled]{background:#c5c1d9}
/* #ifdef MP-WEIXIN */
.history-panel{height:calc(100vh - 112rpx - 104rpx - env(safe-area-inset-bottom));padding-bottom:34rpx}.messages{height:calc(100vh - 112rpx - 190rpx - 104rpx - env(safe-area-inset-bottom))}.composer{bottom:calc(104rpx + env(safe-area-inset-bottom))}.error-bar{bottom:calc(294rpx + env(safe-area-inset-bottom))}
/* #endif */
</style>
