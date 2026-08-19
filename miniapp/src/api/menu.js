import { request } from './request'

const MENU_CACHE_KEY = 'workbench_apps_cache_v2'

export function listApps() {
  return request({
    url: '/navigation',
    method: 'GET'
  })
}

export function readMenuCache() {
  return uni.getStorageSync(MENU_CACHE_KEY) || null
}

export function writeMenuCache(value) {
  uni.setStorageSync(MENU_CACHE_KEY, { ...value, savedAt: Date.now() })
}

export function invalidateMenuCache() {
  uni.removeStorageSync(MENU_CACHE_KEY)
  uni.removeStorageSync('workbench_apps_cache_v1')
}
