import { request, toQuery } from './request'

const prefix = '/netops2026/radius'

function get(path, params) {
  return request({ url: `${prefix}${path}${toQuery(params)}` })
}

export const getRadiusProfile = (keyword) => get('/profile', { keyword })
