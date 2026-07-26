const { request } = require('./request')

function listApps() {
  return request({
    url: '/workbench/apps',
    method: 'GET'
  })
}

module.exports = {
  listApps
}
