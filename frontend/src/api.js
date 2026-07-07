const API_BASE = 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  runChecks: () => request('/api/checks/run', { method: 'POST' }),
  listRuns: (limit = 20) => request(`/api/checks/runs?limit=${limit}`),
  getRunDetail: (runId) => request(`/api/checks/runs/${runId}`),
  getTrend: (metric, limit = 50) =>
    request(`/api/checks/trend?${metric ? `metric=${metric}&` : ''}limit=${limit}`),
  listAlerts: (resolved, limit = 50) =>
    request(`/api/alerts?limit=${limit}${resolved !== undefined ? `&resolved=${resolved}` : ''}`),
  resolveAlert: (alertId) => request(`/api/alerts/${alertId}/resolve`, { method: 'PATCH' }),
  alertsSummary: () => request('/api/alerts/summary'),
  healthSummary: () => request('/api/reports/health-summary'),
  failingChecks: () => request('/api/reports/failing-checks'),
}
