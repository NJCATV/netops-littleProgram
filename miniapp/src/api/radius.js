import { request, toQuery } from './request'

const prefix = '/radius'

function get(path, params) {
  return request({ url: `${prefix}${path}${toQuery(params)}` })
}

export const getRadiusProfile = (keyword) => get('/profile', { keyword })
