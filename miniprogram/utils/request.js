const DEFAULT_BASE_URL = 'https://anbo.njcatv.net:5772/wx/api'

function getBaseUrl() {
  const app = getApp()
  return (app.globalData && app.globalData.apiBaseUrl) || DEFAULT_BASE_URL
}

function request(options) {
  const token = wx.getStorageSync('access_token')
  const header = Object.assign(
    {
      'content-type': 'application/json'
    },
    options.header || {}
  )

  if (token) {
    header.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBaseUrl()}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header,
      success(response) {
        const body = response.data || {}

        if (response.statusCode === 401) {
          wx.removeStorageSync('access_token')
          wx.removeStorageSync('current_user')
        }

        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) {
          resolve(body.data)
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

module.exports = {
  request
}
