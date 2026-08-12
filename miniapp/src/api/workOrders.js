import { getBaseUrl, request, toQuery } from './request'

export function listWorkOrders(params = {}) {
  return request({ url: `/work-orders${toQuery(params)}`, method: 'GET' })
}

export function getWorkOrder(id) {
  return request({ url: `/work-orders/${id}`, method: 'GET' })
}

export function runWorkOrderAction(id, action, data = {}) {
  return request({ url: `/work-orders/${id}/actions/${action}`, method: 'POST', data })
}

export function startInstallation(id) {
  return request({ url: `/work-orders/${id}/installation/attempts`, method: 'POST', data: {} })
}

export function runInstallationAgent(id, agentCode) {
  return request({ url: `/work-orders/${id}/installation/agents/${agentCode}/run`, method: 'POST', data: {} })
}

export function submitInstallation(id) {
  return request({ url: `/work-orders/${id}/installation/submit`, method: 'POST', data: {} })
}

export function listOssTodo(params = {}) {
  return request({ url: `/oss/work-orders${toQuery(params)}`, method: 'GET' })
}

export function claimOssOrder(order) {
  return request({ url: '/oss/work-orders/claim', method: 'POST', data: { order } })
}

export function returnOssOrder(id, data = {}) {
  return request({ url: `/oss/work-orders/${id}/return`, method: 'POST', data })
}

function upload(path, filePath, name, formData = {}) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${getBaseUrl()}${path}`,
      filePath,
      name,
      formData,
      header: { Authorization: `Bearer ${uni.getStorageSync('access_token') || ''}` },
      success(response) {
        let body = {}
        try {
          body = typeof response.data === 'string' ? JSON.parse(response.data) : response.data
        } catch (error) {
          reject(new Error('服务器返回内容无法解析'))
          return
        }
        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) {
          resolve(body.data || {})
          return
        }
        reject(new Error(body.message || `上传失败(${response.statusCode})`))
      },
      fail(error) {
        reject(new Error(error.errMsg || '上传失败'))
      }
    })
  })
}

export function uploadInstallationPhoto(id, agentCode, filePath) {
  return upload(`/work-orders/${id}/installation/photos`, filePath, 'photo', {
    agent_code: agentCode,
    photo_role: 'standard',
    replace_active: '1'
  })
}

export function uploadInstallationSignature(id, filePath, signerName) {
  return upload(`/work-orders/${id}/installation/signature`, filePath, 'signature', {
    signer_name: signerName || ''
  })
}
