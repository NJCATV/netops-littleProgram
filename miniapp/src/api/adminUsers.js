import { request, toQuery } from './request'

export function listUsers(params) {
  return request({
    url: `/admin/users${toQuery(params)}`,
    method: 'GET'
  })
}

export function userOptions() {
  return request({
    url: '/admin/users/options',
    method: 'GET'
  })
}

export function createUser(data) {
  return request({
    url: '/admin/users',
    method: 'POST',
    data
  })
}

export function updateUser(id, data) {
  return request({
    url: `/admin/users/${id}`,
    method: 'PUT',
    data
  })
}

export function enableUser(id) {
  return request({
    url: `/admin/users/${id}/enable`,
    method: 'POST'
  })
}

export function disableUser(id) {
  return request({
    url: `/admin/users/${id}/disable`,
    method: 'POST'
  })
}

export function resetPassword(id) {
  return request({
    url: `/admin/users/${id}/reset-password`,
    method: 'POST'
  })
}
