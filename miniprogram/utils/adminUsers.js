const { request } = require('./request')

function listUsers(params) {
  return request({
    url: `/admin/users${toQuery(params)}`,
    method: 'GET'
  })
}

function userOptions() {
  return request({
    url: '/admin/users/options',
    method: 'GET'
  })
}

function createUser(data) {
  return request({
    url: '/admin/users',
    method: 'POST',
    data
  })
}

function updateUser(id, data) {
  return request({
    url: `/admin/users/${id}`,
    method: 'PUT',
    data
  })
}

function enableUser(id) {
  return request({
    url: `/admin/users/${id}/enable`,
    method: 'POST'
  })
}

function disableUser(id) {
  return request({
    url: `/admin/users/${id}/disable`,
    method: 'POST'
  })
}

function resetPassword(id) {
  return request({
    url: `/admin/users/${id}/reset-password`,
    method: 'POST'
  })
}

function toQuery(params) {
  const pairs = Object.keys(params || {})
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
  return pairs.length ? `?${pairs.join('&')}` : ''
}

module.exports = {
  createUser,
  disableUser,
  enableUser,
  listUsers,
  resetPassword,
  updateUser,
  userOptions
}
