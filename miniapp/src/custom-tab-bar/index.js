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
      const pages = getCurrentPages()
      const current = pages[pages.length - 1]
      const route = current && `/${current.route}`
      const selected = this.data.tabs.findIndex((item) => item.pagePath === route)
      if (selected >= 0) this.setData({ selected })
    }
  },
  methods: {
    switchTab(event) {
      const index = Number(event.currentTarget.dataset.index)
      const item = this.data.tabs[index]
      if (!item || index === this.data.selected) return
      const previous = this.data.selected
      this.setData({ selected: index })
      wx.switchTab({
        url: item.pagePath,
        fail: () => this.setData({ selected: previous })
      })
    }
  }
})
