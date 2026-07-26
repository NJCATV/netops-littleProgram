import { request } from './request'

export function listMenus() {
  return request({
    url: '/admin/menus',
    method: 'GET'
  })
}

export function createMenu(data) {
  return request({
    url: '/admin/menus',
    method: 'POST',
    data
  })
}

export function updateMenu(id, data) {
  return request({
    url: `/admin/menus/${id}`,
    method: 'PUT',
    data
  })
}

export function enableMenu(id) {
  return request({
    url: `/admin/menus/${id}/enable`,
    method: 'POST'
  })
}

export function disableMenu(id) {
  return request({
    url: `/admin/menus/${id}/disable`,
    method: 'POST'
  })
}
