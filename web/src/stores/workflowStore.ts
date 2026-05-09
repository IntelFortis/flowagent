import { create } from 'zustand'
import { Node, Edge, OnNodesChange, OnEdgesChange, applyNodeChanges, applyEdgeChanges, Connection, addEdge } from '@xyflow/react'
import { api } from '../api/client'
import { getLayoutedElements } from '../utils/autoLayout'
import { getSettings } from '../components/SettingsModal'

export interface WorkflowNode extends Node {
  data: {
    type: string
    label: string
    config: Record<string, any>
    category: string
    color: string
    icon: string
  }
}

interface ExecutionState {
  status: string
  nodeStatuses: Record<string, string>
  logs: any[]
  results: Record<string, any>
}

interface HistoryEntry {
  nodes: WorkflowNode[]
  edges: Edge[]
}

export interface ValidationIssue {
  level: 'error' | 'warning'
  nodeId?: string
  message: string
}

interface WorkflowStore {
  // Workflows
  workflows: any[]
  currentWorkflowId: string | null
  workflowName: string
  workflowDescription: string

  // Canvas
  nodes: WorkflowNode[]
  edges: Edge[]
  selectedNodeId: string | null
  selectedEdgeId: string | null

  // Clipboard
  clipboard: WorkflowNode[] | null

  // History
  history: HistoryEntry[]
  historyIndex: number

  // Execution
  execution: ExecutionState | null
  isRunning: boolean

  // Validation
  validationIssues: ValidationIssue[]
  showValidation: boolean

  // Bottom panel
  bottomTab: 'logs' | 'output' | 'errors' | 'history'
  bottomOpen: boolean

  // Dirty state
  isDirty: boolean

  // Error state
  loadError: string | null

  // Actions
  loadWorkflows: () => Promise<void>
  createWorkflow: (name: string) => Promise<string>
  loadWorkflow: (id: string) => Promise<void>
  saveWorkflow: () => Promise<void>
  deleteWorkflow: (id: string) => Promise<void>

  setWorkflowName: (name: string) => void
  setWorkflowDescription: (desc: string) => void
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect: (connection: Connection) => void
  addNode: (node: WorkflowNode) => void
  removeNode: (id: string) => void
  selectNode: (id: string | null) => void
  selectEdge: (id: string | null) => void
  removeEdge: (id: string) => void
  updateNodeConfig: (id: string, config: Record<string, any>) => void

  runWorkflow: () => Promise<void>
  stopWorkflow: () => Promise<void>
  pollStatus: () => Promise<void>

  setBottomTab: (tab: 'logs' | 'output' | 'errors' | 'history') => void
  toggleBottomPanel: () => void

  autoLayout: (direction?: 'LR' | 'TB') => void
  duplicateWorkflow: (id: string) => Promise<string>
  clearCanvas: () => void

  undo: () => void
  redo: () => void
  canUndo: () => boolean
  canRedo: () => boolean

  copyNode: (id: string) => void
  pasteNodes: () => void
  canPaste: () => boolean

  validateWorkflow: () => ValidationIssue[]
  setShowValidation: (show: boolean) => void
}

let pollTimer: ReturnType<typeof setInterval> | null = null
const MAX_HISTORY = 50

function pushHistory(get: () => WorkflowStore, set: (partial: Partial<WorkflowStore>) => void) {
  const { nodes, edges, history, historyIndex } = get()
  const entry: HistoryEntry = { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }
  const newHistory = history.slice(0, historyIndex + 1)
  newHistory.push(entry)
  if (newHistory.length > MAX_HISTORY) newHistory.shift()
  set({ history: newHistory, historyIndex: newHistory.length - 1 })
}

export const useWorkflowStore = create<WorkflowStore>((set, get) => ({
  workflows: [],
  currentWorkflowId: null,
  workflowName: '未命名工作流',
  workflowDescription: '',
  nodes: [],
  edges: [],
  selectedNodeId: null,
  selectedEdgeId: null,
  history: [],
  historyIndex: -1,
  execution: null,
  isRunning: false,
  validationIssues: [],
  showValidation: false,
  bottomTab: 'logs',
  bottomOpen: false,
  clipboard: null,
  isDirty: false,
  loadError: null,

  loadWorkflows: async () => {
    try {
      const workflows = await api.listWorkflows()
      set({ workflows })
    } catch {
      // Server not running or network error
    }
  },

  createWorkflow: async (name: string) => {
    const wf = await api.createWorkflow({ name, nodes: [], edges: [] })
    set({ currentWorkflowId: wf.id, workflowName: wf.name, workflowDescription: '', nodes: [], edges: [], execution: null })
    get().loadWorkflows()
    return wf.id
  },

  loadWorkflow: async (id: string) => {
    try {
      set({ loadError: null })
      const wf = await api.getWorkflow(id)
      const nodes = (wf.nodes || []).map((n: any) => ({
        ...n,
        type: 'custom',
        data: { ...n.data, color: n.data.color || '#3b82f6', icon: n.data.icon || 'box' },
      }))
      set({
        currentWorkflowId: wf.id,
        workflowName: wf.name,
        workflowDescription: wf.description || '',
        nodes,
        edges: wf.edges || [],
        execution: null,
        selectedNodeId: null,
        history: [],
        historyIndex: -1,
        isDirty: false,
        loadError: null,
      })
    } catch (e: any) {
      set({ loadError: e.message || '加载工作流失败' })
    }
  },

  saveWorkflow: async () => {
    const { currentWorkflowId, workflowName, workflowDescription, nodes, edges } = get()
    if (!currentWorkflowId) return
    await api.updateWorkflow(currentWorkflowId, {
      name: workflowName,
      description: workflowDescription,
      nodes: nodes.map(n => ({ id: n.id, type: n.data.type, position: n.position, data: n.data })),
      edges,
    })
    set({ isDirty: false })
  },

  deleteWorkflow: async (id: string) => {
    await api.deleteWorkflow(id)
    const { currentWorkflowId } = get()
    if (currentWorkflowId === id) {
      set({ currentWorkflowId: null, workflowName: '未命名工作流', workflowDescription: '', nodes: [], edges: [], execution: null })
    }
    get().loadWorkflows()
  },

  setWorkflowName: (name: string) => set({ workflowName: name, isDirty: true }),
  setWorkflowDescription: (desc: string) => set({ workflowDescription: desc, isDirty: true }),

  onNodesChange: (changes) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) as WorkflowNode[], isDirty: true })
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges), isDirty: true })
  },

  onConnect: (connection) => {
    const { nodes, edges } = get()
    const sourceNode = nodes.find(n => n.id === connection.source)
    const targetNode = nodes.find(n => n.id === connection.target)

    // Validation: no self-loops
    if (connection.source === connection.target) return

    // Validation: no duplicate edges
    const exists = edges.some(e =>
      e.source === connection.source &&
      e.target === connection.target &&
      e.sourceHandle === connection.sourceHandle
    )
    if (exists) return

    // Validation: trigger nodes can't have inputs (handled by Handle presence)
    // Validation: output nodes can't have outputs (handled by Handle presence)

    // Validation: only one edge per target handle (except for condition branches)
    if (connection.targetHandle && sourceNode?.data.type !== 'condition') {
      const targetOccupied = edges.some(e =>
        e.target === connection.target && e.targetHandle === connection.targetHandle
      )
      if (targetOccupied) return
    }

    const edgeData: any = {}

    // Auto-label condition node edges
    if (sourceNode?.data.type === 'condition' && connection.sourceHandle) {
      edgeData.label = connection.sourceHandle === 'true' ? '是' : '否'
      edgeData.color = connection.sourceHandle === 'true' ? '#22c55e' : '#ef4444'
    }

    pushHistory(get, set)
    set({
      edges: addEdge({
        ...connection,
        type: 'custom',
        animated: true,
        style: { stroke: '#64748b', strokeWidth: 2 },
        data: edgeData,
      }, get().edges),
      isDirty: true,
    })
  },

  addNode: (node: WorkflowNode) => {
    pushHistory(get, set)
    set({ nodes: [...get().nodes, node], isDirty: true })
  },

  removeNode: (id: string) => {
    pushHistory(get, set)
    set({
      nodes: get().nodes.filter(n => n.id !== id),
      edges: get().edges.filter(e => e.source !== id && e.target !== id),
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId,
      isDirty: true,
    })
  },

  selectNode: (id) => set({ selectedNodeId: id, selectedEdgeId: null }),

  selectEdge: (id) => set({ selectedEdgeId: id, selectedNodeId: null }),

  removeEdge: (id: string) => {
    pushHistory(get, set)
    set({
      edges: get().edges.filter(e => e.id !== id),
      selectedEdgeId: get().selectedEdgeId === id ? null : get().selectedEdgeId,
      isDirty: true,
    })
  },

  updateNodeConfig: (id, config) => {
    set({
      nodes: get().nodes.map(n =>
        n.id === id ? { ...n, data: { ...n.data, config: { ...n.data.config, ...config } } } : n
      ),
      isDirty: true,
    })
  },

  runWorkflow: async () => {
    // Validate first
    const issues = get().validateWorkflow()
    const errors = issues.filter(i => i.level === 'error')
    if (errors.length > 0) {
      set({ validationIssues: issues, showValidation: true })
      return
    }

    let { currentWorkflowId } = get()

    // Auto-create workflow if none exists
    if (!currentWorkflowId) {
      const name = get().workflowName || '未命名工作流'
      currentWorkflowId = await get().createWorkflow(name)
    }

    try {
      set({ showValidation: false })
      await get().saveWorkflow()
      const settings = getSettings()
      const exec = await api.runWorkflow(currentWorkflowId, {
        global_api_key: settings.api_key,
        global_api_base: settings.api_base,
        global_model: settings.default_model,
      })
      set({
        isRunning: true,
        bottomOpen: true,
        bottomTab: 'logs',
        execution: {
          status: exec.status,
          nodeStatuses: exec.node_statuses || {},
          logs: exec.logs || [],
          results: exec.results || {},
        },
      })

      // Start polling
      if (pollTimer) clearInterval(pollTimer)
      pollTimer = setInterval(() => get().pollStatus(), 1000)
    } catch (e: any) {
      console.error('Run workflow failed:', e)
      set({
        bottomOpen: true,
        execution: {
          status: 'failed',
          nodeStatuses: {},
          logs: [{ time: new Date().toISOString(), node: '', message: `运行失败: ${e.message || e}`, level: 'error' }],
          results: {},
        },
      })
    }
  },

  stopWorkflow: async () => {
    const { currentWorkflowId } = get()
    if (!currentWorkflowId) return
    await api.stopWorkflow(currentWorkflowId)
    set({ isRunning: false })
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  },

  pollStatus: async () => {
    const { currentWorkflowId } = get()
    if (!currentWorkflowId) return
    try {
      const result = await api.getWorkflowStatus(currentWorkflowId)
      if (result.execution) {
        set({
          execution: {
            status: result.execution.status,
            nodeStatuses: result.execution.node_statuses || {},
            logs: result.execution.logs || [],
            results: result.execution.results || {},
          },
          nodes: get().nodes.map(n => ({
            ...n,
            data: {
              ...n.data,
              status: result.execution.node_statuses?.[n.id] || 'pending',
            },
          })),
        })

        if (['completed', 'failed', 'stopped'].includes(result.execution.status)) {
          set({ isRunning: false })
          if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
        }
      }
    } catch {}
  },

  setBottomTab: (tab) => set({ bottomTab: tab }),
  toggleBottomPanel: () => set({ bottomOpen: !get().bottomOpen }),

  autoLayout: (direction = 'LR') => {
    const { nodes, edges } = get()
    if (nodes.length === 0) return
    pushHistory(get, set)
    const { nodes: layoutedNodes } = getLayoutedElements([...nodes], [...edges], direction)
    set({ nodes: layoutedNodes as WorkflowNode[] })
  },

  duplicateWorkflow: async (id: string) => {
    const wf = await api.getWorkflow(id)
    const newWf = await api.createWorkflow({
      name: `${wf.name} (副本)`,
      nodes: wf.nodes || [],
      edges: wf.edges || [],
    })
    get().loadWorkflows()
    return newWf.id
  },

  clearCanvas: () => {
    pushHistory(get, set)
    set({ nodes: [], edges: [], selectedNodeId: null, execution: null })
  },

  undo: () => {
    const { history, historyIndex, nodes, edges } = get()
    if (historyIndex < 0) return
    const entry = history[historyIndex]
    // Save current state to history for redo
    const newHistory = [...history]
    newHistory[historyIndex] = { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }
    set({
      nodes: entry.nodes,
      edges: entry.edges,
      history: newHistory,
      historyIndex: historyIndex - 1,
    })
  },

  redo: () => {
    const { history, historyIndex, nodes, edges } = get()
    if (historyIndex >= history.length - 1) return
    const entry = history[historyIndex + 1]
    // Save current state back
    const newHistory = [...history]
    newHistory[historyIndex + 1] = { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }
    set({
      nodes: entry.nodes,
      edges: entry.edges,
      history: newHistory,
      historyIndex: historyIndex + 1,
    })
  },

  canUndo: () => get().historyIndex >= 0,
  canRedo: () => get().historyIndex < get().history.length - 1,

  copyNode: (id: string) => {
    const node = get().nodes.find(n => n.id === id)
    if (node) {
      set({ clipboard: [JSON.parse(JSON.stringify(node))] })
    }
  },

  pasteNodes: () => {
    const { clipboard, nodes } = get()
    if (!clipboard || clipboard.length === 0) return
    pushHistory(get, set)
    const newNodes = clipboard.map(n => ({
      ...n,
      id: `${n.data.type}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      position: { x: n.position.x + 60, y: n.position.y + 60 },
      data: { ...n.data },
    }))
    set({
      nodes: [...nodes, ...newNodes],
      selectedNodeId: newNodes[0].id,
    })
  },

  canPaste: () => {
    const clip = get().clipboard
    return clip !== null && clip.length > 0
  },

  validateWorkflow: () => {
    const { nodes, edges } = get()
    const issues: ValidationIssue[] = []

    if (nodes.length === 0) {
      issues.push({ level: 'error', message: '工作流为空，请添加至少一个节点' })
      return issues
    }

    // Check for disconnected nodes (no edges at all)
    const connectedNodes = new Set<string>()
    edges.forEach(e => { connectedNodes.add(e.source); connectedNodes.add(e.target) })
    const disconnected = nodes.filter(n => !connectedNodes.has(n.id) && nodes.length > 1)
    disconnected.forEach(n => {
      issues.push({ level: 'warning', nodeId: n.id, message: `节点「${n.data.label}」未连接到任何其他节点` })
    })

    // Check for trigger nodes (should be entry points)
    const triggers = nodes.filter(n => n.data.category === 'trigger')
    if (triggers.length === 0) {
      issues.push({ level: 'warning', message: '没有触发器节点，工作流可能无法自动启动' })
    }

    // Check for nodes with no incoming edges (except triggers)
    const hasIncoming = new Set(edges.map(e => e.target))
    const noInput = nodes.filter(n => n.data.category !== 'trigger' && !hasIncoming.has(n.id))
    noInput.forEach(n => {
      issues.push({ level: 'error', nodeId: n.id, message: `节点「${n.data.label}」没有输入连接` })
    })

    // Check required config fields
    const requiredFields: Record<string, string[]> = {
      http_request: ['url'],
      knowledge_base: ['documents'],
      condition: ['field'],
      set_variable: ['name'],
      code: ['code'],
      send_email: ['to'],
      webhook_response: ['url'],
      webhook_trigger: ['url_path'],
    }
    nodes.forEach(n => {
      const required = requiredFields[n.data.type] || []
      required.forEach(field => {
        if (!n.data.config[field] || n.data.config[field].toString().trim() === '') {
          issues.push({ level: 'error', nodeId: n.id, message: `节点「${n.data.label}」的必填字段「${field}」未填写` })
        }
      })
    })

    return issues
  },

  setShowValidation: (show: boolean) => set({ showValidation: show }),
}))
