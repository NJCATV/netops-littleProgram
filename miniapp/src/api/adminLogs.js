import { request, toQuery } from './request'

export function listLogs(params) {
  return request({
    url: `/admin/logs${toQuery(params)}`,
    method: 'GET'
  })
}
