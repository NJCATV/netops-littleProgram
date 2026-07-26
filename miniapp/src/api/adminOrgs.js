import { request } from './request'

export function listOrgs() {
  return request({
    url: '/admin/orgs/tree',
    method: 'GET'
  })
}

export function createOrg(data) {
  return request({
    url: '/admin/orgs',
    method: 'POST',
    data
  })
}

export function updateOrg(id, data) {
  return request({
    url: `/admin/orgs/${id}`,
    method: 'PUT',
    data
  })
}

export function enableOrg(id) {
  return request({
    url: `/admin/orgs/${id}/enable`,
    method: 'POST'
  })
}

export function disableOrg(id) {
  return request({
    url: `/admin/orgs/${id}/disable`,
    method: 'POST'
  })
}

export function deleteOrg(id) {
  return request({
    url: `/admin/orgs/${id}`,
    method: 'DELETE'
  })
}
