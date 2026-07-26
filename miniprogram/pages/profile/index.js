const { clearSession, getMe, logout } = require('../../utils/auth')

Page({
  data: {
    user: {},
    userInitial: '用'
  },

  onLoad() {
    this.loadMe()
  },

  loadMe() {
    const user = wx.getStorageSync('current_user') || {}
    this.setData({ user, userInitial: this.initialOf(user.real_name) })
    getMe()
      .then((data) => {
        const currentUser = data.user || {}
        this.setData({ user: currentUser, userInitial: this.initialOf(currentUser.real_name) })
      })
      .catch(() => {
        clearSession()
        wx.redirectTo({ url: '/pages/index/index' })
      })
  },

  goWorkbench() {
    wx.redirectTo({ url: '/pages/workbench/index' })
  },

  goChangePassword() {
    wx.navigateTo({ url: '/pages/auth/change-password/index' })
  },

  goBindOss() {
    wx.navigateTo({ url: '/pages/auth/bind-oss/index' })
  },

  onLogout() {
    logout().finally(() => {
      wx.redirectTo({ url: '/pages/index/index' })
    })
  },

  initialOf(name) {
    return (name || '用').slice(0, 1)
  }
})
