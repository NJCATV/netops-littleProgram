const { request } = require('./request')

function saveSession(data) {
  if (data.access_token) {
    wx.setStorageSync('access_token', data.access_token)
  }
  if (data.user) {
    wx.setStorageSync('current_user', data.user)
  }
}

function clearSession() {
  wx.removeStorageSync('access_token')
  wx.removeStorageSync('current_user')
}

function login(account, password) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data: {
      account,
      password
    }
  }).then((data) => {
    saveSession(data)
    return data
  })
}

function bindOss(ossAccount, ossPassword) {
  return request({
    url: '/auth/bind-oss',
    method: 'POST',
    data: {
      oss_account: ossAccount,
      oss_password: ossPassword
    }
  }).then((data) => {
    saveSession(data)
    return data
  })
}

function changePassword(oldPassword, newPassword) {
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

function logout() {
  return request({
    url: '/auth/logout',
    method: 'POST'
  }).finally(() => {
    clearSession()
  })
}

function navigateByNextAction(nextAction) {
  if (nextAction === 'bind_oss') {
    wx.redirectTo({
      url: '/pages/auth/bind-oss/index'
    })
    return
  }

  if (nextAction === 'change_password') {
    wx.redirectTo({
      url: '/pages/auth/change-password/index'
    })
    return
  }

  const user = wx.getStorageSync('current_user') || {}
  if (user.role_code === 'super_admin' || user.role_code === 'org_admin') {
    wx.redirectTo({
      url: '/pages/workbench/index'
    })
    return
  }

  wx.redirectTo({
    url: '/pages/workbench/index'
  })
}

function getMe() {
  return request({
    url: '/auth/me',
    method: 'GET'
  }).then((data) => {
    saveSession(data)
    return data
  })
}

module.exports = {
  bindOss,
  changePassword,
  clearSession,
  getMe,
  login,
  logout,
  navigateByNextAction,
  saveSession
}
