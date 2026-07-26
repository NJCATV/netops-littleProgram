Page({
  onShareAppMessage() {
    return {
      title: '江苏有线南京分公司智维助手',
      path: '/pages/index/index'
    }
  },

  onShareTimeline() {
    return {
      title: '江苏有线南京分公司智维助手',
      path: '/pages/index/index'
    }
  },

  goWatermarkCamera() {
    wx.navigateTo({
      url: '/pages/watermark-camera/index'
    })
  },

  goIpCalculator() {
    wx.navigateTo({
      url: '/pages/ip-calculator/ip-calculator'
    })
  }
})
