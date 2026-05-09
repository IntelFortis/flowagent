const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (err) {
    throw new Error('无法连接到服务器，请确认服务已启动')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `请求失败 (${res.status})`)
  }
  return res.json()
}

export const api = {
  // Workflows
  listWorkflows: () => request<any[]>('/workflows'),
  createWorkflow: (data: any) => request<any>('/workflows', { method: 'POST', body: JSON.stringify(data) }),
  getWorkflow: (id: string) => request<any>(`/workflows/${id}`),
  updateWorkflow: (id: string, data: any) => request<any>(`/workflows/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteWorkflow: (id: string) => request<any>(`/workflows/${id}`, { method: 'DELETE' }),
  runWorkflow: (id: string, options?: any) => request<any>(`/workflows/${id}/run`, { method: 'POST', body: JSON.stringify(options || {}) }),
  stopWorkflow: (id: string) => request<any>(`/workflows/${id}/stop`, { method: 'POST' }),
  getWorkflowStatus: (id: string) => request<any>(`/workflows/${id}/status`),
  listExecutions: (id: string) => request<any[]>(`/workflows/${id}/executions`),
  getExecution: (execId: string) => request<any>(`/executions/${execId}`),

  // Nodes
  listNodes: () => request<any[]>('/nodes'),
  listCategories: () => request<any[]>('/nodes/categories'),

  // Models
  listAliases: () => request<any>('/models/aliases'),
  createAlias: (data: any) => request<any>('/models/aliases', { method: 'POST', body: JSON.stringify(data) }),
  deleteAlias: (alias: string) => request<any>(`/models/aliases/${alias}`, { method: 'DELETE' }),
}
