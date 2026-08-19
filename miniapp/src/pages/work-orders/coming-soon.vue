<template>
  <view class="page coming-page">
    <view class="coming-card">
      <view class="coming-icon">装</view>
      <view class="coming-title">敬请期待</view>
      <view class="coming-desc">智能装维功能正在完善中</view>
      <button class="back-button" @tap="goBack">返回菜单</button>
    </view>
  </view>
</template>

<script setup>
function goBack() {
  uni.navigateBack({
    fail: () => uni.switchTab({ url: '/pages/workbench/index' })
  })
}
</script>

<style scoped>
.coming-page {
  display: flex;
  min-height: 72vh;
  align-items: center;
  justify-content: center;
  padding: 48rpx 34rpx 140rpx;
}

.coming-card {
  width: 100%;
  padding: 72rpx 36rpx 54rpx;
  border: 1rpx solid #e1e8f0;
  border-radius: 30rpx;
  background: #ffffff;
  box-shadow: 0 18rpx 48rpx rgba(31, 59, 92, 0.08);
  text-align: center;
}

.coming-icon {
  display: flex;
  width: 112rpx;
  height: 112rpx;
  margin: 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 32rpx;
  background: linear-gradient(145deg, #1b84e8, #2452c8);
  box-shadow: 0 16rpx 30rpx rgba(32, 98, 200, 0.24);
  color: #ffffff;
  font-size: 42rpx;
  font-weight: 750;
}

.coming-title {
  margin-top: 34rpx;
  color: #1d2c40;
  font-size: 42rpx;
  font-weight: 750;
}

.coming-desc {
  margin-top: 14rpx;
  color: #8793a2;
  font-size: 25rpx;
}

.back-button {
  width: 260rpx;
  margin-top: 44rpx;
  border: 0;
  border-radius: 99rpx;
  background: #1769e8;
  color: #ffffff;
  font-size: 25rpx;
}

.back-button::after {
  border: 0;
}
</style>
