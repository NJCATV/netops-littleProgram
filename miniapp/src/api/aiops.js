import { request, toQuery } from './request'

const prefix = '/aiops'

function get(path, params) {
  return request({ url: `${prefix}${path}${toQuery(params)}` })
}

function send(path, method, data) {
  return request({ url: `${prefix}${path}`, method, data })
}

export const getAiopsRuns = (limit = 30) => get('/ai-runs', { limit })
export const getAiopsRun = (runUid) => get(`/ai-runs/${encodeURIComponent(runUid)}`)
export const getAiopsOverview = (hours = 24) => get('/runtime/overview', { hours })
export const getAiopsFreshness = () => get('/runtime/freshness')

export const getAiChatSessions = (limit = 30) => get('/fault-kb/chat/sessions', { limit })
export const getAiChatSession = (id) => get(`/fault-kb/chat/sessions/${id}`)
export const deleteAiChatSession = (id) => send(`/fault-kb/chat/sessions/${id}`, 'DELETE')
export const sendAiChatMessage = (message, sessionId) => send('/fault-kb/chat', 'POST', {
  message,
  limit: 10,
  session_id: sessionId || null
})
