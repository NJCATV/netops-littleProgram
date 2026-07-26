<script>
export default {
  onLaunch() {
    uni.removeStorageSync('oss_reminder_skipped')
    const token = uni.getStorageSync('access_token')
    if (!token) {
      return
    }
  }
}
</script>

<style>
page {
  min-height: 100%;
  background: #f3f6f9;
  color: #172133;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 28rpx;
}

view,
text,
input,
button {
  box-sizing: border-box;
}

button {
  margin: 0;
  padding: 0;
  border-radius: 4rpx;
  line-height: normal;
}

button::after {
  border: 0;
}

.page {
  min-height: 100vh;
  padding: 24rpx 24rpx 56rpx;
  background: #f3f6f9;
}

.panel {
  border: 1rpx solid #e4e9ef;
  border-radius: 18rpx;
  background: #ffffff;
}

.field-label {
  margin-bottom: 12rpx;
  color: #2b3642;
  font-size: 26rpx;
  font-weight: 600;
}

.input {
  width: 100%;
  min-height: 84rpx;
  padding: 0 22rpx;
  border: 1rpx solid #d9e1ea;
  border-radius: 4rpx;
  background: #ffffff;
  color: #1f2933;
  font-size: 28rpx;
}

.placeholder {
  color: #98a4b2;
}

.primary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 84rpx;
  line-height: 84rpx;
  border-radius: 12rpx;
  background: #2269c8;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
}

.secondary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 72rpx;
  line-height: 72rpx;
  border: 1rpx solid #d8e0e8;
  border-radius: 12rpx;
  background: #ffffff;
  color: #285b8f;
  font-size: 26rpx;
}

.danger-text {
  color: #c9352b;
}

.muted {
  color: #6b7785;
}

.status-text {
  padding: 36rpx 0;
  color: #6b7785;
  font-size: 26rpx;
  text-align: center;
}

.netops-page {
  min-height: 100vh;
  padding: 24rpx 24rpx 64rpx;
  background: #f3f6f9;
}

.section-card {
  overflow: hidden;
  border: 1rpx solid #e3e9f0;
  border-radius: 18rpx;
  background: #ffffff;
}

.section-card + .section-card { margin-top: 20rpx; }

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  min-height: 86rpx;
  padding: 0 24rpx;
  border-bottom: 1rpx solid #edf1f5;
}

.section-head-title { color: #172133; font-size: 28rpx; font-weight: 700; }
.section-head-meta { color: #7c8897; font-size: 22rpx; }

.search-bar {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 16rpx;
  border: 1rpx solid #e0e7ef;
  border-radius: 16rpx;
  background: #fff;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 70rpx;
  padding: 0 20rpx;
  border-radius: 12rpx;
  background: #f2f5f8;
  color: #1f2d3d;
  font-size: 26rpx;
}

.search-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 116rpx;
  height: 70rpx;
  border-radius: 12rpx;
  background: #2269c8;
  color: #fff;
  font-size: 25rpx;
  font-weight: 650;
}

.load-more { padding: 28rpx; color: #4d6f9b; font-size: 24rpx; text-align: center; }
</style>
