import { request, toQuery } from './request'

const prefix = '/aiops'

function get(path, params) {
  return request({ url: `${prefix}${path}${toQuery(params)}` })
}

function send(path, method, data) {
  return request({ url: `${prefix}${path}`, method, data })
}

export const getAiopsResource = (path, params) => get(path, params)
export const sendAiopsResource = (path, method, data) => send(path, method, data)

export const getAiopsRuns = (limit = 30) => get('/ai-runs', { limit })
export const getAiopsRun = (runUid) => get(`/ai-runs/${encodeURIComponent(runUid)}`)
export const getAiopsOverview = (hours = 24) => get('/runtime/overview', { hours })
export const getAiopsFreshness = () => get('/runtime/freshness')
export const getKnowledgeSummary = () => get('/fault-kb/summary')
export const getKnowledgeItems = (type, params = {}) => get(`/fault-kb/${type === 'documents' ? 'reports' : type}`, {
  ...params,
  ...(type === 'reports' ? { source_type: 'formal_fault_report' } : {}),
  ...(type === 'documents' ? { source_type: 'document_kb' } : {})
})

export const getAiChatSessions = (limit = 30) => get('/fault-kb/chat/sessions', { limit })
export const getAiChatSession = (id) => get(`/fault-kb/chat/sessions/${id}`)
export const deleteAiChatSession = (id) => send(`/fault-kb/chat/sessions/${id}`, 'DELETE')
export const sendAiChatMessage = (message, sessionId) => send('/fault-kb/chat', 'POST', {
  message,
  limit: 10,
  session_id: sessionId || null
})
