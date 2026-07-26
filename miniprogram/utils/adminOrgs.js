const { request } = require('./request')

function orgTree() {
  return request({
    url: '/admin/orgs/tree',
    method: 'GET'
  })
}

function createOrg(data) {
  return request({
    url: '/admin/orgs',
    method: 'POST',
    data
  })
}

function updateOrg(id, data) {
  return request({
    url: `/admin/orgs/${id}`,
    method: 'PUT',
    data
  })
}

function disableOrg(id) {
  return request({
    url: `/admin/orgs/${id}/disable`,
    method: 'POST'
  })
}

module.exports = {
  createOrg,
  disableOrg,
  orgTree,
  updateOrg
}
