const { login, navigateByNextAction } = require('../../utils/auth')

Page({
  data: {
    account: '',
    password: '',
    passwordVisible: false,
    passwordHidden: true,
    canSubmit: false,
    submitting: false
  },

  goTools() {
    wx.navigateTo({
      url: '/pages/tools/index'
    })
  },

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

  onAccountInput(event) {
    this.setData({
      account: event.detail.value
    }, this.updateSubmitState)
  },

  onPasswordInput(event) {
    this.setData({
      password: event.detail.value
    }, this.updateSubmitState)
  },

  togglePassword() {
    const passwordVisible = !this.data.passwordVisible

    this.setData({
      passwordVisible,
      passwordHidden: !passwordVisible
    })
  },

  updateSubmitState() {
    const canSubmit = this.data.account.length > 0 && this.data.password.length > 0

    this.setData({ canSubmit })
  },

  onLoginTap() {
    if (!this.data.canSubmit || this.data.submitting) {
      return
    }

    this.setData({ submitting: true })
    login(this.data.account, this.data.password)
      .then((data) => {
        navigateByNextAction(data.next_action)
      })
      .catch((error) => {
        wx.showToast({
          title: error.message,
          icon: 'none'
        })
      })
      .finally(() => {
        this.setData({ submitting: false })
      })
  },

  onRegisterTap() {
    this.showComingSoon()
  },

  showComingSoon() {
    wx.showToast({
      title: '加速开发中，敬请期待',
      icon: 'none'
    })
  }
})
