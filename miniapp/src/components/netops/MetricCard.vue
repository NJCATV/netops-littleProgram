<template>
  <view class="metric" :class="`tone-${tone}`">
    <view class="metric-top">
      <text class="metric-label">{{ label }}</text>
      <view class="metric-dot" />
    </view>
    <view class="metric-value">{{ value ?? '--' }}</view>
    <view v-if="hint" class="metric-hint">{{ hint }}</view>
  </view>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '--' },
  hint: { type: String, default: '' },
  tone: { type: String, default: 'blue' }
})
</script>

<style scoped>
.metric {
  min-width: 0;
  padding: 24rpx;
  border: 1rpx solid #e4e9ef;
  border-radius: 18rpx;
  background: #fff;
}

.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.metric-label {
  color: #667385;
  font-size: 23rpx;
}

.metric-dot {
  width: 13rpx;
  height: 13rpx;
  border-radius: 50%;
  background: #3276dc;
}

.metric-value {
  margin-top: 14rpx;
  color: #172133;
  font-size: 42rpx;
  font-weight: 750;
  letter-spacing: -1rpx;
}

.metric-hint {
  margin-top: 8rpx;
  overflow: hidden;
  color: #8994a3;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tone-green .metric-dot { background: #15906f; }
.tone-orange .metric-dot { background: #d8861d; }
.tone-red .metric-dot { background: #d6504a; }
.tone-purple .metric-dot { background: #7459d9; }
</style>
