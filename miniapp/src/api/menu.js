import { request } from './request'

export function listApps() {
  return request({
    url: '/navigation',
    method: 'GET'
  })
}
