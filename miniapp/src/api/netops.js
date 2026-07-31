import { getBaseUrl, request, toQuery } from './request'

const prefix = ''

function get(path, params, header) {
  return request({ url: `${prefix}${path}${toQuery(params)}`, header })
}

function send(path, method, data) {
  return request({ url: `${prefix}${path}`, method, data })
}

export const getNetopsDashboard = () => get('/dashboard')

export const searchOnu = (params) => get('/onu/search', params)
export const getOnuHistory = (params) => get('/onu/history', params)
export const getRealtimePower = (data) => send('/onu/realtime-power', 'POST', data)
export const getOnuQuality = (params) => get('/onu/quality-daily', params)

export function downloadOnuQuality(params) {
  return new Promise((resolve, reject) => {
    uni.downloadFile({
      url: `${getBaseUrl()}${prefix}/onu/quality-daily/export${toQuery(params)}`,
      header: { Authorization: `Bearer ${uni.getStorageSync('access_token') || ''}` },
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) resolve(response.tempFilePath)
        else reject(new Error(`导出失败(${response.statusCode})`))
      },
      fail(error) { reject(new Error(error.errMsg || '导出失败')) }
    })
  })
}

export const getOltPerformance = (params) => get('/olt/performance', params)
export const getOltPerformanceDetail = (params) => get('/olt/performance/detail', params)
export const getOltPerformanceHistory = (params) => get('/olt/performance/history', params)

export const getCollectorOverview = () => get('/collector/overview')
export const getCollectorTasks = (params) => get('/collector/tasks', params)
export const getCollectorDevices = (params) => get('/collector/devices', params)
export const getCollectorHistory = (params) => get('/collector/history', params)

export const getOltDeviceOptions = () => get('/olt/device-options')
export const getOltDevices = (params) => get('/olt/devices', params)
export const createOltDevice = (data) => send('/olt/devices', 'POST', data)
export const updateOltDevice = (id, data) => send(`/olt/devices/${id}`, 'PUT', data)
export const probeOlt = (data) => send('/olt/probe', 'POST', data)

export const searchCm = (params) => get('/cm/search', params)
export const getCmtsOptions = () => get('/cmts/device-options')
export const getCmtsDevices = (params) => get('/cmts/devices', params)
export const createCmtsDevice = (data) => send('/cmts/devices', 'POST', data)
export const updateCmtsDevice = (id, data) => send(`/cmts/devices/${id}`, 'PUT', data)

export const createBossAccess = (password) => request({ url: `${prefix}/boss/access`, method: 'POST', data: { password } })
export const getBossUsers = (params, accessToken) => get('/boss/users', params, { 'X-Boss-Access': accessToken })
export const getBossUserDetail = (id, accessToken) => get(`/boss/users/${id}`, {}, { 'X-Boss-Access': accessToken })

export function importBossUsers(filePath, accessToken) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getBaseUrl()}${prefix}/boss/users/import`,
      filePath,
      name: 'file',
      header: { Authorization: `Bearer ${uni.getStorageSync('access_token') || ''}`, 'X-Boss-Access': accessToken || '' },
      success(response) {
        let body = {}
        try { body = JSON.parse(response.data || '{}') } catch (_) {}
        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) resolve(body.data || {})
        else reject(new Error(body.message || `导入失败(${response.statusCode})`))
      },
      fail(error) { reject(new Error(error.errMsg || '导入失败')) }
    })
  })
}
export const getDeviceOrganizations = () => get('/device-orgs')
export const createDeviceOrganization = (data) => send('/device-orgs', 'POST', data)
export const updateDeviceOrganization = (id, data) => send(`/device-orgs/${id}`, 'PUT', data)
export const deleteDeviceOrganization = (id) => send(`/device-orgs/${id}`, 'DELETE')
export const getOrganizationMappings = () => get('/organization-mappings')
export const updateOrganizationMapping = (id, data) => send(`/organization-mappings/${id}`, 'PUT', data)

export const getNetopsSettings = () => get('/settings')
export const saveOnuQualityRule = (data) => send('/settings/quality/onu-rx-rule', 'POST', data)
export const saveOltPerformanceRule = (data) => send('/settings/performance/olt-rule', 'POST', data)
