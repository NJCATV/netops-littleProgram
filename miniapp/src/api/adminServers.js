import { request, toQuery } from './request'

export function listServers(params = {}) {
  return request({
    url: `/admin/servers${toQuery(params)}`,
    method: 'GET'
  })
}

export function serverShareOptions() {
  return request({
    url: '/admin/servers/share-options',
    method: 'GET'
  })
}

export function createServer(data) {
  return request({
    url: '/admin/servers',
    method: 'POST',
    data
  })
}

export function updateServer(id, data) {
  return request({
    url: `/admin/servers/${id}`,
    method: 'PUT',
    data
  })
}

export function setServerStatus(id, status) {
  return request({
    url: `/admin/servers/${id}/status`,
    method: 'POST',
    data: { status }
  })
}

export function listCredentials(serverId) {
  return request({
    url: `/admin/servers/${serverId}/credentials`,
    method: 'GET'
  })
}

export function createCredential(serverId, data) {
  return request({
    url: `/admin/servers/${serverId}/credentials`,
    method: 'POST',
    data
  })
}

export function updateCredential(id, data) {
  return request({
    url: `/admin/servers/credentials/${id}`,
    method: 'PUT',
    data
  })
}

export function deleteCredential(id) {
  return request({
    url: `/admin/servers/credentials/${id}`,
    method: 'DELETE'
  })
}

export function revealCredential(id) {
  return request({
    url: `/admin/servers/credentials/${id}/reveal`,
    method: 'POST'
  })
}
