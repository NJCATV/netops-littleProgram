<template>
  <view class="empty-state">
    <view class="empty-mark">{{ mark }}</view>
    <view class="empty-title">{{ title }}</view>
    <view v-if="description" class="empty-description">{{ description }}</view>
  </view>
</template>

<script setup>
defineProps({
  mark: { type: String, default: '·' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.empty-state {
  padding: 72rpx 28rpx;
  color: #7b8796;
  text-align: center;
}

.empty-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  margin: 0 auto 20rpx;
  border-radius: 50%;
  background: #eef3f8;
  color: #4a6f9e;
  font-size: 42rpx;
  font-weight: 700;
}

.empty-title { color: #465468; font-size: 27rpx; font-weight: 650; }
.empty-description { margin-top: 10rpx; font-size: 23rpx; line-height: 1.55; }
</style>
