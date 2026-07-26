const DEFAULT_BASE_URL = 'https://anbo.njcatv.net:5772/wx/api'

export function getBaseUrl() {
  return uni.getStorageSync('api_base_url') || DEFAULT_BASE_URL
}

export function setBaseUrl(baseUrl) {
  if (baseUrl) {
    uni.setStorageSync('api_base_url', baseUrl.replace(/\/$/, ''))
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
}
