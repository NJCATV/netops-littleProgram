<template>
  <text class="badge" :class="badgeClass">{{ label }}</text>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [String, Number, Boolean], default: '' },
  text: { type: String, default: '' }
})

const normalized = computed(() => String(props.value ?? '').toLowerCase())
const label = computed(() => {
  if (props.text) return props.text
  const labels = {
    success: '成功', normal: '正常', online: '在线', active: '启用', true: '正常', '1': '正常',
    running: '运行中', partial: '部分成功', warning: '告警', critical: '严重',
    failed: '失败', fail: '失败', error: '异常', offline: '离线', disabled: '停用', false: '异常', '0': '异常',
    missing: '未采集', pending: '等待中'
  }
  return labels[normalized.value] || props.value || '--'
})

const badgeClass = computed(() => {
  const value = normalized.value
  if (['success', 'normal', 'online', 'active', 'true', '1'].includes(value)) return 'is-ok'
  if (['running', 'partial', 'pending'].includes(value)) return 'is-info'
  if (['warning', '告警', '质差'].some((item) => value.includes(item))) return 'is-warn'
  if (['failed', 'fail', 'error', 'offline', 'disabled', 'false', '0', 'critical'].includes(value)) return 'is-danger'
  return 'is-neutral'
})
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  min-height: 38rpx;
  padding: 0 14rpx;
  border-radius: 99rpx;
  background: #eef2f6;
  color: #5e6b7b;
  font-size: 20rpx;
  line-height: 38rpx;
  white-space: nowrap;
}

.is-ok { background: #e8f6f1; color: #117658; }
.is-info { background: #eaf2ff; color: #2c66bd; }
.is-warn { background: #fff3df; color: #a86812; }
.is-danger { background: #fdeceb; color: #bd433d; }
</style>
