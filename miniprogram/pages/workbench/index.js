const { getMe } = require('../../utils/auth')
const { listApps } = require('../../utils/workbench')

const iconMap = {
  camera: 'camera',
  calculator: 'root-list',
  search: 'search',
  calendar: 'calendar',
  'folder-search': 'folder-search',
  usergroup: 'usergroup',
  tree: 'tree-round-dot',
  app: 'app',
  setting: 'setting'
}

Page({
  data: {
    user: {},
    userInitial: '用',
    commonApps: [],
    allApps: [],
    loading: false
  },

  onLoad() {
    this.loadPage()
  },

  onShow() {
    this.loadApps()
  },

  loadPage() {
    const user = wx.getStorageSync('current_user') || {}
    this.setData({ user, userInitial: this.initialOf(user.real_name) })
    getMe()
      .then((data) => {
        const currentUser = data.user || {}
        this.setData({ user: currentUser, userInitial: this.initialOf(currentUser.real_name) })
        this.loadApps()
      })
      .catch(() => {
        wx.redirectTo({ url: '/pages/index/index' })
      })
  },

  loadApps() {
    this.setData({ loading: true })
    listApps()
      .then((data) => {
        const items = (data.items || []).map((item) => Object.assign({}, item, {
          iconName: iconMap[item.icon] || 'app'
        }))
        const commonApps = items.filter((item) => item.group_name === '我的常用').slice(0, 4)
        this.setData({
          commonApps,
          allApps: items
        })
      })
      .catch((error) => this.toast(error.message))
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  openApp(event) {
    const index = Number(event.currentTarget.dataset.index)
    const source = event.currentTarget.dataset.source
    const list = source === 'common' ? this.data.commonApps : this.data.allApps
    const app = list[index]
    if (!app) {
      return
    }
    if (!app.path) {
      this.toast('功能开发中，敬请期待')
      return
    }
    wx.navigateTo({ url: app.path })
  },

  goManageApps() {
    if (this.data.user.role_code === 'super_admin') {
      wx.navigateTo({ url: '/pages/admin/menus/index' })
      return
    }
    this.toast('功能开发中，敬请期待')
  },

  goProfile() {
    wx.redirectTo({ url: '/pages/profile/index' })
  },

  toast(title) {
    wx.showToast({ title, icon: 'none' })
  },

  initialOf(name) {
    return (name || '用').slice(0, 1)
  }
})
