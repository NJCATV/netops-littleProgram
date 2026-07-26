import { request } from './request'

export function listApps() {
  return request({
    url: '/workbench/apps',
    method: 'GET'
  })
}
