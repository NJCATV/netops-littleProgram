import { clearSessionStorage, getBaseUrl, request } from './request'

const LAST_LOGIN_ACCOUNT_KEY = 'last_login_account'
const AUTO_LOGIN_SUSPENDED_KEY = 'auto_login_suspended'

export function saveSession(data = {}) {
  if (data.access_token) {
    uni.setStorageSync('access_token', data.access_token)
  }
  if (data.user) {
    uni.setStorageSync('current_user', data.user)
  }
}

export function saveLastLoginAccount(account) {
  if (account) {
    uni.setStorageSync(LAST_LOGIN_ACCOUNT_KEY, account)
  }
}

export function saveLoginPreferences(account, password, options = {}) {
  saveLastLoginAccount(account)
  uni.removeStorageSync(AUTO_LOGIN_SUSPENDED_KEY)
  // 清理旧版本曾保存的明文密码和自动登录开关；后续只依赖有时效的访问令牌。
  uni.removeStorageSync('last_login_password')
  uni.removeStorageSync('remember_login_password')
  uni.removeStorageSync('auto_login_enabled')
}

export function getLastLoginAccount() {
  return uni.getStorageSync(LAST_LOGIN_ACCOUNT_KEY) || ''
}

export function getLastLoginPassword() {
  return ''
}

export function isRememberPasswordEnabled() {
  return false
}

export function isAutoLoginEnabled() {
  return false
}

export function getStoredUser() {
  return uni.getStorageSync('current_user') || {}
}

export function resolveAssetUrl(url) {
  const value = String(url || '').trim()
  if (!value) {
    return ''
  }
  const baseUrl = getBaseUrl().replace(/\/+$/, '')
  const originMatch = baseUrl.match(/^(https?:\/\/[^/]+)/i)
  const origin = originMatch ? originMatch[1] : ''
  const absoluteMatch = value.match(/^https?:\/\/[^/]+(\/[^?#]*)/i)
  if (/^https?:\/\//i.test(value) && !absoluteMatch) return value
  let path = absoluteMatch ? absoluteMatch[1] : value
  path = path.startsWith('/') ? path : `/${path}`

  // 兼容历史记录中的 /api/files、/api/netops2026/files 和当前 /files 三种格式。
  const avatarMatch = path.match(/^\/(?:api\/(?:netops2026\/)?)*files\/avatars\/(.+)$/i)
  if (avatarMatch) {
    return `${baseUrl}/files/avatars/${avatarMatch[1]}`
  }
  if (absoluteMatch) return value
  if (/^\/api\//i.test(path) && origin) {
    return `${origin}${path}`
  }
  return `${baseUrl}${path}`
}

export function hasToken() {
  return Boolean(uni.getStorageSync('access_token'))
}

export function login(account, password, options = {}) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data: { account, password }
  }).then((data) => {
    saveSession(data)
    saveLoginPreferences(account, password, options)
    return data
  })
}

export function getMe() {
  return request({
    url: '/auth/me',
    method: 'GET'
  }).then((data) => {
    saveSession(data)
    return data
  })
}

export function bindOss(ossAccount, ossPassword, useOssPasswordForLogin = false) {
  return request({
    url: '/auth/bind-oss',
    method: 'POST',
    data: {
      oss_account: ossAccount,
      oss_password: ossPassword,
      use_oss_password_for_login: useOssPasswordForLogin
    }
  }).then((data) => {
    saveSession(data)
    return data
  })
}

export function changePassword(oldPassword, newPassword) {
  return request({
    url: '/auth/change-password',
    method: 'POST',
    data: {
      old_password: oldPassword,
      new_password: newPassword
    }
  }).then((data) => {
    saveSession(data)
    return data
  })
}

export function uploadAvatar(filePath) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getBaseUrl()}/files/avatar`,
      filePath,
      name: 'avatar',
      header: {
        Authorization: `Bearer ${uni.getStorageSync('access_token') || ''}`
      },
      success(response) {
        let body = {}
        try {
          body = typeof response.data === 'string' ? JSON.parse(response.data) : response.data
        } catch (error) {
          reject(new Error('头像上传返回异常'))
          return
        }

        if (response.statusCode === 401) {
          clearSessionStorage()
        }

        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) {
          saveSession(body.data || {})
          resolve(body.data || {})
          return
        }

        reject(new Error(body.message || `头像上传失败(${response.statusCode})`))
      },
      fail(error) {
        reject(new Error(error.errMsg || '头像上传失败'))
      }
    })
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'POST'
  }).catch(() => ({})).finally(() => {
    clearSessionStorage()
    uni.setStorageSync(AUTO_LOGIN_SUSPENDED_KEY, true)
  })
}

export function redirectByNextAction(nextAction) {
  if (nextAction === 'change_password') {
    uni.redirectTo({ url: '/pages/auth/change-password/index' })
    return
  }

  uni.switchTab({ url: '/pages/workbench/index' })
}

export function requireLogin() {
  if (!hasToken()) {
    uni.reLaunch({ url: '/pages/login/index' })
    return Promise.reject(new Error('未登录'))
  }

  return getMe().catch((error) => {
    clearSessionStorage()
    uni.reLaunch({ url: '/pages/login/index' })
    throw error
  })
}
