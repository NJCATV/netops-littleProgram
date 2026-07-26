const { changePassword, navigateByNextAction } = require('../../../utils/auth')

Page({
  data: {
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    canSubmit: false,
    submitting: false
  },

  onOldPasswordInput(event) {
    this.setData({
      oldPassword: event.detail.value
    }, this.updateSubmitState)
  },

  onNewPasswordInput(event) {
    this.setData({
      newPassword: event.detail.value
    }, this.updateSubmitState)
  },

  onConfirmPasswordInput(event) {
    this.setData({
      confirmPassword: event.detail.value
    }, this.updateSubmitState)
  },

  updateSubmitState() {
    const canSubmit = this.data.oldPassword.length > 0 &&
      this.data.newPassword.length >= 8 &&
      this.data.confirmPassword.length >= 8

    this.setData({ canSubmit })
  },

  onSubmit() {
    if (!this.data.canSubmit || this.data.submitting) {
      return
    }

    if (this.data.newPassword !== this.data.confirmPassword) {
      wx.showToast({
        title: '两次输入的新密码不一致',
        icon: 'none'
      })
      return
    }

    this.setData({ submitting: true })
    changePassword(this.data.oldPassword, this.data.newPassword)
      .then((data) => {
        wx.showToast({
          title: '修改成功',
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
