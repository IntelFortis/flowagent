import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkflowStore } from '../stores/workflowStore'
import { api } from '../api/client'

const TEMPLATES = [
  {
    name: 'HTTP 数据获取与日志',
    description: '手动触发 → HTTP 请求 → 日志输出',
    icon: '🌐',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'http_1', type: 'custom', position: { x: 300, y: 150 }, data: { type: 'http_request', label: 'HTTP 请求', config: { url: 'https://jsonplaceholder.typicode.com/posts/1', method: 'GET' }, category: 'data', color: '#3b82f6', icon: 'globe' }},
      { id: 'log_1', type: 'custom', position: { x: 550, y: 150 }, data: { type: 'log_output', label: '日志输出', config: { message: '获取数据完成' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'http_1' },
      { id: 'e2', source: 'http_1', target: 'log_1' },
    ],
  },
  {
    name: '数据过滤流水线',
    description: '触发 → HTTP → JSON 解析 → 数据过滤 → 日志',
    icon: '🔍',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'http_1', type: 'custom', position: { x: 250, y: 150 }, data: { type: 'http_request', label: 'HTTP 请求', config: { url: 'https://jsonplaceholder.typicode.com/posts', method: 'GET' }, category: 'data', color: '#3b82f6', icon: 'globe' }},
      { id: 'filter_1', type: 'custom', position: { x: 450, y: 150 }, data: { type: 'data_filter', label: '数据过滤', config: { field: 'userId', operator: 'equals', value: '1' }, category: 'data', color: '#3b82f6', icon: 'filter' }},
      { id: 'log_1', type: 'custom', position: { x: 650, y: 150 }, data: { type: 'log_output', label: '日志输出', config: { message: '过滤完成' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'http_1' },
      { id: 'e2', source: 'http_1', target: 'filter_1' },
      { id: 'e3', source: 'filter_1', target: 'log_1' },
    ],
  },
  {
    name: '代码执行工作流',
    description: '触发 → Python 代码执行 → 日志',
    icon: '💻',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'code_1', type: 'custom', position: { x: 300, y: 150 }, data: { type: 'code', label: 'Python 代码', config: { code: 'def main(input_data):\n    return {"result": 42, "message": "Hello from Python!"}' }, category: 'logic', color: '#f59e0b', icon: 'code' }},
      { id: 'log_1', type: 'custom', position: { x: 550, y: 150 }, data: { type: 'log_output', label: '日志输出', config: { message: '' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'code_1' },
      { id: 'e2', source: 'code_1', target: 'log_1' },
    ],
  },
  {
    name: 'AI 对话',
    description: '触发 → LLM 聊天 → 日志输出',
    icon: '🤖',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'llm_1', type: 'custom', position: { x: 300, y: 150 }, data: { type: 'llm_chat', label: 'LLM 聊天', config: { model: 'gpt-4o', system_prompt: '你是一个有用的助手', user_prompt: '用一句话介绍 FlowAgent', temperature: 0.7 }, category: 'ai', color: '#8b5cf6', icon: 'brain' }},
      { id: 'log_1', type: 'custom', position: { x: 550, y: 150 }, data: { type: 'log_output', label: '日志输出', config: { message: '' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'llm_1' },
      { id: 'e2', source: 'llm_1', target: 'log_1' },
    ],
  },
  {
    name: '条件分支工作流',
    description: '触发 → HTTP → 条件判断 → 是/否分支',
    icon: '⑂',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'http_1', type: 'custom', position: { x: 250, y: 150 }, data: { type: 'http_request', label: '获取用户', config: { url: 'https://jsonplaceholder.typicode.com/users/1', method: 'GET' }, category: 'data', color: '#3b82f6', icon: 'globe' }},
      { id: 'cond_1', type: 'custom', position: { x: 450, y: 150 }, data: { type: 'condition', label: '检查邮箱', config: { field: 'email', operator: 'contains', value: '@' }, category: 'logic', color: '#f59e0b', icon: 'git-branch' }},
      { id: 'log_ok', type: 'custom', position: { x: 700, y: 50 }, data: { type: 'log_output', label: '邮箱有效', config: { message: '邮箱格式正确' }, category: 'output', color: '#22c55e', icon: 'terminal' }},
      { id: 'log_fail', type: 'custom', position: { x: 700, y: 250 }, data: { type: 'log_output', label: '邮箱无效', config: { message: '邮箱格式错误' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'http_1' },
      { id: 'e2', source: 'http_1', target: 'cond_1' },
      { id: 'e3', source: 'cond_1', sourceHandle: 'true', target: 'log_ok', data: { label: '是', color: '#22c55e' } },
      { id: 'e4', source: 'cond_1', sourceHandle: 'false', target: 'log_fail', data: { label: '否', color: '#ef4444' } },
    ],
  },
  {
    name: '数据转换管道',
    description: '触发 → HTTP → 数据转换 → 聚合统计 → 日志',
    icon: '📊',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'http_1', type: 'custom', position: { x: 250, y: 150 }, data: { type: 'http_request', label: '获取数据', config: { url: 'https://jsonplaceholder.typicode.com/posts', method: 'GET' }, category: 'data', color: '#3b82f6', icon: 'globe' }},
      { id: 'transform_1', type: 'custom', position: { x: 450, y: 150 }, data: { type: 'data_transform', label: '提取标题', config: { expression: 'data["title"]' }, category: 'data', color: '#3b82f6', icon: 'shuffle' }},
      { id: 'agg_1', type: 'custom', position: { x: 650, y: 150 }, data: { type: 'aggregate', label: '统计数量', config: { operation: 'count' }, category: 'data', color: '#3b82f6', icon: 'bar-chart' }},
      { id: 'log_1', type: 'custom', position: { x: 850, y: 150 }, data: { type: 'log_output', label: '输出结果', config: { message: '' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'http_1' },
      { id: 'e2', source: 'http_1', target: 'transform_1' },
      { id: 'e3', source: 'transform_1', target: 'agg_1' },
      { id: 'e4', source: 'agg_1', target: 'log_1' },
    ],
  },
  {
    name: '文本处理流水线',
    description: '触发 → 变量设置 → 文本分割 → 文本拼接 → 日志',
    icon: '📝',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'var_1', type: 'custom', position: { x: 250, y: 150 }, data: { type: 'set_variable', label: '设置文本', config: { name: 'text', value: 'Hello World From FlowAgent' }, category: 'data', color: '#3b82f6', icon: 'variable' }},
      { id: 'split_1', type: 'custom', position: { x: 450, y: 150 }, data: { type: 'text_split', label: '按空格分割', config: { delimiter: ' ' }, category: 'data', color: '#3b82f6', icon: 'scissors' }},
      { id: 'join_1', type: 'custom', position: { x: 650, y: 150 }, data: { type: 'text_join', label: '用逗号拼接', config: { delimiter: ', ' }, category: 'data', color: '#3b82f6', icon: 'link' }},
      { id: 'log_1', type: 'custom', position: { x: 850, y: 150 }, data: { type: 'log_output', label: '输出结果', config: { message: '' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'var_1' },
      { id: 'e2', source: 'var_1', target: 'split_1' },
      { id: 'e3', source: 'split_1', target: 'join_1' },
      { id: 'e4', source: 'join_1', target: 'log_1' },
    ],
  },
  {
    name: 'Webhook 回调',
    description: 'Webhook 触发 → 处理数据 → 返回响应',
    icon: '🔗',
    nodes: [
      { id: 'webhook_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'webhook', label: 'Webhook 触发', config: { path: '/api/hook' }, category: 'trigger', color: '#10b981', icon: 'webhook' }},
      { id: 'code_1', type: 'custom', position: { x: 300, y: 150 }, data: { type: 'code', label: '处理数据', config: { code: 'def main(input_data):\n    return {"processed": True, "data": input_data}' }, category: 'logic', color: '#f59e0b', icon: 'code' }},
      { id: 'hook_out', type: 'custom', position: { x: 550, y: 150 }, data: { type: 'webhook_response', label: '返回响应', config: { status_code: 200 }, category: 'output', color: '#ef4444', icon: 'send' }},
    ],
    edges: [
      { id: 'e1', source: 'webhook_1', target: 'code_1' },
      { id: 'e2', source: 'code_1', target: 'hook_out' },
    ],
  },
  {
    name: 'AI 数据分析',
    description: '获取数据 → AI 分析 → 输出结果，演示变量引用',
    icon: '🧠',
    nodes: [
      { id: 'trigger_1', type: 'custom', position: { x: 50, y: 150 }, data: { type: 'manual_trigger', label: '手动触发', config: {}, category: 'trigger', color: '#10b981', icon: 'play' }},
      { id: 'http_1', type: 'custom', position: { x: 250, y: 150 }, data: { type: 'http_request', label: '获取数据', config: { url: 'https://jsonplaceholder.typicode.com/posts/1', method: 'GET' }, category: 'data', color: '#3b82f6', icon: 'globe' }},
      { id: 'llm_1', type: 'custom', position: { x: 500, y: 150 }, data: { type: 'llm_chat', label: 'AI 分析', config: { model: 'gpt-4o', system_prompt: '你是一个数据分析专家。请分析以下数据并给出洞察。', user_prompt: '请分析这个数据：{{获取数据.output.body}}', temperature: 0.7 }, category: 'ai', color: '#8b5cf6', icon: 'brain' }},
      { id: 'log_1', type: 'custom', position: { x: 750, y: 150 }, data: { type: 'log_output', label: '输出分析结果', config: { message: '{{AI 分析.output.response}}' }, category: 'output', color: '#ef4444', icon: 'terminal' }},
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'http_1' },
      { id: 'e2', source: 'http_1', target: 'llm_1' },
      { id: 'e3', source: 'llm_1', target: 'log_1' },
    ],
  },
]

function TemplatePreview({ template, children }: { template: typeof TEMPLATES[0]; children: React.ReactNode }) {
  const [show, setShow] = useState(false)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const handleEnter = () => {
    clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect()
        setPos({ x: rect.right + 12, y: rect.top })
      }
      setShow(true)
    }, 400)
  }

  const handleLeave = () => {
    clearTimeout(timeoutRef.current)
    setShow(false)
  }

  // Build mini flow layout
  const nodePositions: { x: number; y: number; color: string; label: string }[] = []
  const edgeLines: { x1: number; y1: number; x2: number; y2: number }[] = []

  // Simple left-to-right layout
  const nodeGap = 90
  const startX = 10
  const centerY = 30
  template.nodes.forEach((n, i) => {
    nodePositions.push({
      x: startX + i * nodeGap,
      y: centerY,
      color: n.data.color,
      label: n.data.label.slice(0, 4),
    })
  })
  template.edges.forEach(e => {
    const srcIdx = template.nodes.findIndex(n => n.id === e.source)
    const tgtIdx = template.nodes.findIndex(n => n.id === e.target)
    if (srcIdx >= 0 && tgtIdx >= 0) {
      edgeLines.push({
        x1: startX + srcIdx * nodeGap + 28,
        y1: centerY,
        x2: startX + tgtIdx * nodeGap,
        y2: centerY,
      })
    }
  })

  const svgWidth = Math.max(template.nodes.length * nodeGap + 30, 120)

  return (
    <div ref={triggerRef} onMouseEnter={handleEnter} onMouseLeave={handleLeave} className="relative">
      {children}
      {show && (
        <div
          className="fixed z-50 pointer-events-none"
          style={{ left: Math.min(pos.x, window.innerWidth - 260), top: Math.min(pos.y, window.innerHeight - 120) }}
        >
          <div className="bg-[#0f172a] border border-[#334155] rounded-lg shadow-2xl p-3 w-60">
            <p className="text-xs text-[#94a3b8] mb-2 font-medium">流程预览</p>
            <svg width={svgWidth} height={60} className="mx-auto">
              {edgeLines.map((line, i) => (
                <line key={i} x1={line.x1} y1={line.y1} x2={line.x2} y2={line.y2} stroke="#475569" strokeWidth="1.5" markerEnd="url(#arrow)" />
              ))}
              <defs>
                <marker id="arrow" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6" fill="#475569" />
                </marker>
              </defs>
              {nodePositions.map((np, i) => (
                <g key={i}>
                  <rect x={np.x} y={np.y - 12} width={28} height={24} rx={5} fill={np.color + '30'} stroke={np.color + '60'} strokeWidth="1" />
                  <text x={np.x + 14} y={np.y + 4} textAnchor="middle" fill={np.color} fontSize="8" fontFamily="sans-serif">{np.label}</text>
                </g>
              ))}
            </svg>
            <div className="mt-2 space-y-1">
              {template.nodes.map((n, i) => (
                <div key={i} className="flex items-center gap-1.5 text-[10px]">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: n.data.color }} />
                  <span className="text-[#64748b]">{n.data.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const { workflows, loadWorkflows, createWorkflow, deleteWorkflow, duplicateWorkflow } = useWorkflowStore()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [search, setSearch] = useState('')
  const [serverError, setServerError] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<any>(null)

  const filteredWorkflows = workflows.filter((wf: any) =>
    wf.name.toLowerCase().includes(search.toLowerCase()) ||
    (wf.description || '').toLowerCase().includes(search.toLowerCase()) ||
    (wf.tags || []).some((t: string) => t.toLowerCase().includes(search.toLowerCase()))
  )

  useEffect(() => {
    loadWorkflows().catch(() => setServerError(true))
  }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    const id = await createWorkflow(newName.trim())
    setNewName('')
    setShowCreate(false)
    navigate(`/editor/${id}`)
  }

  const handleUseTemplate = async (template: typeof TEMPLATES[0]) => {
    const wf = await api.createWorkflow({ name: template.name, nodes: template.nodes, edges: template.edges })
    loadWorkflows()
    navigate(`/editor/${wf.id}`)
  }

  return (
    <div className="min-h-screen bg-[#0f172a]">
      {/* Header */}
      <header className="border-b border-[#334155] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-white">FlowAgent</h1>
            <div className="relative ml-4">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="搜索工作流..."
                className="pl-9 pr-4 py-2 bg-[#1e293b] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-blue-500 w-64"
              />
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建工作流
          </button>
        </div>
      </header>

      {/* Server error banner */}
      {serverError && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center gap-2 text-sm text-red-400">
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            无法连接到服务器，请运行 <code className="bg-red-500/20 px-1.5 py-0.5 rounded text-xs font-mono">python -m flowagent ui</code> 启动服务
          </div>
        </div>
      )}

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Templates */}
        <h2 className="text-2xl font-bold text-white mb-2">快速开始</h2>
        <p className="text-[#94a3b8] mb-5">选择一个模板快速创建工作流，或从空白开始</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-10">
          {TEMPLATES.map((tpl, i) => (
            <TemplatePreview key={i} template={tpl}>
              <div
                onClick={() => handleUseTemplate(tpl)}
                className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 hover:border-blue-500/50 hover:bg-[#1e293b]/80 transition-all cursor-pointer group"
              >
                <div className="text-2xl mb-2">{tpl.icon}</div>
                <h3 className="font-semibold text-white text-sm mb-1 group-hover:text-blue-400 transition-colors">{tpl.name}</h3>
                <p className="text-xs text-[#64748b]">{tpl.description}</p>
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-[10px] text-[#475569]">{tpl.nodes.length} 节点</span>
                  <span className="text-[10px] text-[#334155]">·</span>
                  <span className="text-[10px] text-[#475569]">{tpl.edges.length} 连接</span>
                </div>
              </div>
            </TemplatePreview>
          ))}
        </div>

        <div className="flex items-center justify-between mb-5">
          <h2 className="text-2xl font-bold text-white">我的工作流</h2>
          {workflows.length > 0 && (
            <span className="text-xs text-[#64748b]">{workflows.length} 个工作流</span>
          )}
        </div>

        {filteredWorkflows.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#1e293b] flex items-center justify-center">
              <svg className="w-8 h-8 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p className="text-[#94a3b8] text-lg mb-2">{search ? '没有匹配的工作流' : '还没有工作流'}</p>
            <p className="text-[#64748b] mb-6">{search ? '尝试其他关键词' : '点击「新建工作流」开始创建你的第一个自动化流程'}</p>
            {!search && (
              <button
                onClick={() => setShowCreate(true)}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                开始创建
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredWorkflows.map((wf: any) => (
              <div
                key={wf.id}
                className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-[#475569] transition-colors cursor-pointer group"
                onClick={() => navigate(`/editor/${wf.id}`)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      wf.status === 'completed' ? 'bg-green-500' :
                      wf.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                      wf.status === 'failed' ? 'bg-red-500' : 'bg-[#475569]'
                    }`} />
                    <h3 className="font-semibold text-white">{wf.name}</h3>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={async (e) => { e.stopPropagation(); const id = await duplicateWorkflow(wf.id); navigate(`/editor/${id}`) }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-[#334155] rounded transition-all"
                      title="复制工作流"
                    >
                      <svg className="w-4 h-4 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteTarget(wf) }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-[#334155] rounded transition-all"
                      title="删除工作流"
                    >
                      <svg className="w-4 h-4 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
                <p className="text-[#94a3b8] text-sm mb-3">{wf.description || '暂无描述'}</p>
                {wf.tags && wf.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {wf.tags.map((tag: string) => (
                      <span key={tag} className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/15 text-blue-400 border border-blue-500/20">{tag}</span>
                    ))}
                  </div>
                )}
                <div className="flex items-center justify-between text-xs text-[#64748b]">
                  <span>{wf.node_count || 0} 个节点</span>
                  {wf.last_execution ? (
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        wf.last_execution.status === 'completed' ? 'bg-green-500' :
                        wf.last_execution.status === 'failed' ? 'bg-red-500' :
                        wf.last_execution.status === 'running' ? 'bg-yellow-500 animate-pulse' : 'bg-[#475569]'
                      }`} />
                      <span className={`text-[10px] ${
                        wf.last_execution.status === 'completed' ? 'text-green-400' :
                        wf.last_execution.status === 'failed' ? 'text-red-400' : 'text-[#64748b]'
                      }`}>
                        {wf.last_execution.status === 'completed' ? '运行成功' :
                         wf.last_execution.status === 'failed' ? '运行失败' :
                         wf.last_execution.status === 'running' ? '运行中' : wf.last_execution.status}
                      </span>
                      {wf.last_execution.duration_ms != null && (
                        <span className="text-[10px] text-[#475569]">{wf.last_execution.duration_ms}ms</span>
                      )}
                    </div>
                  ) : (
                    <span>{wf.updated_at ? new Date(wf.updated_at).toLocaleString('zh-CN') : ''}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setDeleteTarget(null)}>
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6 w-96" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">删除工作流</h3>
                <p className="text-sm text-[#94a3b8]">此操作不可撤销</p>
              </div>
            </div>
            <p className="text-sm text-[#94a3b8] mb-6">
              确定要删除「<span className="text-white font-medium">{deleteTarget.name}</span>」吗？
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)} className="px-4 py-2 text-[#94a3b8] hover:text-white transition-colors">取消</button>
              <button
                onClick={() => { deleteWorkflow(deleteTarget.id); setDeleteTarget(null) }}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6 w-96" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">新建工作流</h3>
            <input
              type="text"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="输入工作流名称"
              className="w-full px-4 py-3 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-blue-500 mb-4"
              autoFocus
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-[#94a3b8] hover:text-white transition-colors">取消</button>
              <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">创建</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
