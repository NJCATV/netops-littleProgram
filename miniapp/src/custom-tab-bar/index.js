Component({
  data: {
    selected: 0,
    tabs: [
      { pagePath: "/pages/workbench/index", text: "菜单", type: "menu" },
      { pagePath: "/pages/netops/ai-assistant/index", text: "一键 AI", type: "ai" },
      { pagePath: "/pages/my/index", text: "我的", type: "profile" }
    ]
  },
  lifetimes: {
    attached() {
      this.syncSelected()
    }
  },
  pageLifetimes: {
    show() {
      this.syncSelected()
    }
  },
  methods: {
    syncSelected() {
      const pages = getCurrentPages()
      const current = pages[pages.length - 1]
      const route = current && `/${current.route}`
      const selected = this.data.tabs.findIndex((item) => item.pagePath === route)
      if (selected >= 0) this.setData({ selected })
    },
    switchTab(event) {
      const index = Number(event.currentTarget.dataset.index)
      const item = this.data.tabs[index]
      if (!item) return
      if (index === this.data.selected) {
        this.syncSelected()
        return
      }
      wx.switchTab({
        url: item.pagePath,
        success: () => this.syncSelected(),
        fail: () => this.syncSelected()
      })
    }
  }
})
