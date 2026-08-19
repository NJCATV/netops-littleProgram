const API_NAMESPACE = '/api/netops2026'
const CANONICAL_ORIGIN = 'https://anbo.njcatv.net:5772'
const DEFAULT_BASE_URL = `${CANONICAL_ORIGIN}${API_NAMESPACE}`

function normalizeBaseUrl(baseUrl) {
  let normalized = String(baseUrl || '').trim().replace(/\/+$/, '')
  if (!normalized) {
    return DEFAULT_BASE_URL
  }
  normalized = normalized.replace(
    /^https?:\/\/172\.31\.1\.233(?::(?:5772|7001))?/i,
    CANONICAL_ORIGIN
  )
  if (/\/wx\/api$/i.test(normalized)) {
    return normalized.replace(/\/wx\/api$/i, API_NAMESPACE)
  }
  if (/\/api$/i.test(normalized)) {
    return `${normalized}/netops2026`
  }
  return normalized
}

export function getBaseUrl() {
  const storedBaseUrl = uni.getStorageSync('api_base_url')
  const baseUrl = normalizeBaseUrl(storedBaseUrl)
  if (storedBaseUrl && storedBaseUrl !== baseUrl) {
    uni.setStorageSync('api_base_url', baseUrl)
  }
  return baseUrl
}

export function setBaseUrl(baseUrl) {
  if (baseUrl) {
    uni.setStorageSync('api_base_url', normalizeBaseUrl(baseUrl))
  }
}

export function request(options) {
  const token = uni.getStorageSync('access_token')
  const header = {
    'content-type': 'application/json',
    ...(options.header || {})
  }

  if (token) {
    header.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${getBaseUrl()}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header,
      success(response) {
        const body = response.data || {}

        if (response.statusCode === 401) {
          clearSessionStorage()
        }

        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) {
          resolve(body.data || {})
          return
        }

        reject(new Error(body.message || `请求失败(${response.statusCode})`))
      },
      fail(error) {
        reject(new Error(error.errMsg || '网络请求失败'))
      }
    })
  })
}

export function toQuery(params = {}) {
  const pairs = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)

  return pairs.length ? `?${pairs.join('&')}` : ''
}

export function clearSessionStorage() {
  uni.removeStorageSync('access_token')
  uni.removeStorageSync('current_user')
  uni.removeStorageSync('workbench_apps_cache_v1')
  uni.removeStorageSync('workbench_apps_cache_v2')
  uni.removeStorageSync('workbench_apps_cache_v3')
}
