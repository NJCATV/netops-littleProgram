import { request } from './request'

export function listApps() {
  return request({
    url: '/navigation',
    method: 'GET'
  })
}

export function invalidateMenuCache() {
  uni.removeStorageSync('workbench_apps_cache_v3')
  uni.removeStorageSync('workbench_apps_cache_v2')
  uni.removeStorageSync('workbench_apps_cache_v1')
}
