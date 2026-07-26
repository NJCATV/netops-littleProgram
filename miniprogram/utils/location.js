function getCurrentLocation() {
  return new Promise((resolve, reject) => {
    wx.getLocation({
      type: 'gcj02',
      success: resolve,
      fail: reject
    })
  })
}

function chooseMapLocation() {
  return new Promise((resolve, reject) => {
    wx.chooseLocation({
      success: resolve,
      fail: reject
    })
  })
}

function formatCoordinateText(latitude, longitude) {
  if (typeof latitude !== 'number' || typeof longitude !== 'number') {
    return ''
  }

  return `纬度 ${latitude.toFixed(6)}，经度 ${longitude.toFixed(6)}`
}

function getLocationErrorMessage(error) {
  const message = error && error.errMsg ? error.errMsg : ''

  if (message.includes('auth deny') || message.includes('authorize')) {
    return '定位权限未开启，请在小程序设置中允许位置信息'
  }

  if (message.includes('cancel')) {
    return '已取消定位操作'
  }

  return '定位失败，请检查权限或稍后重试'
}

module.exports = {
  getCurrentLocation,
  chooseMapLocation,
  formatCoordinateText,
  getLocationErrorMessage
}
