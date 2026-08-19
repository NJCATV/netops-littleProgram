export function syncCustomTabBar(selected) {
  // #ifdef MP-WEIXIN
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  if (current && typeof current.getTabBar === 'function') {
    const tabBar = current.getTabBar()
    if (tabBar) tabBar.setData({ selected })
  }
  // #endif
}
