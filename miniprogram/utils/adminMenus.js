const { request } = require('./request')

function listMenus() {
  return request({
    url: '/admin/menus',
    method: 'GET'
  })
}

function createMenu(data) {
  return request({
    url: '/admin/menus',
    method: 'POST',
    data
  })
}

function updateMenu(id, data) {
  return request({
    url: `/admin/menus/${id}`,
    method: 'PUT',
    data
  })
}

function enableMenu(id) {
  return request({
    url: `/admin/menus/${id}/enable`,
    method: 'POST'
  })
}

function disableMenu(id) {
  return request({
    url: `/admin/menus/${id}/disable`,
    method: 'POST'
  })
}

module.exports = {
  createMenu,
  disableMenu,
  enableMenu,
  listMenus,
  updateMenu
}
