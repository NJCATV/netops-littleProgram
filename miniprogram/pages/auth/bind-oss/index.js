const { bindOss, navigateByNextAction } = require('../../../utils/auth')

Page({
  data: {
    ossAccount: '',
    ossPassword: '',
    passwordVisible: false,
    passwordHidden: true,
    canSubmit: false,
    submitting: false
  },

  onLoad() {
    const user = wx.getStorageSync('current_user') || {}
    this.setData({
      ossAccount: user.oss_account || ''
    }, this.updateSubmitState)
  },

  onOssAccountInput(event) {
    this.setData({
      ossAccount: event.detail.value
    }, this.updateSubmitState)
  },

  onOssPasswordInput(event) {
    this.setData({
      ossPassword: event.detail.value
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
    const canSubmit = this.data.ossAccount.length > 0 && this.data.ossPassword.length > 0
    this.setData({ canSubmit })
  },

  onSubmit() {
    if (!this.data.canSubmit || this.data.submitting) {
      return
    }

    this.setData({ submitting: true })
    bindOss(this.data.ossAccount, this.data.ossPassword)
      .then((data) => {
        wx.showToast({
          title: '绑定成功',
          icon: 'success'
        })
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
  }
})
