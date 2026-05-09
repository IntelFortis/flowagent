import { useEffect, useState } from 'react'
import { useWorkflowStore } from '../stores/workflowStore'
import { buildDefaultConfig } from '../utils/nodeDefaults'

const ICONS: Record<string, string> = {
  play: '▶', webhook: '🔗', clock: '🕐', globe: '🌐', braces: '{ }',
  filter: '▼', shuffle: '⇄', variable: 'x=', brain: '🧠', 'file-text': '📄',
  languages: '🌐', tags: '🏷', 'git-branch': '⑂', timer: '⏱', repeat: '↻',
  code: '</>', mail: '✉', send: '→', download: '⬇', terminal: '>',
  table: '⊞', link: '⊶', scissors: '✂', 'bar-chart': '▮',
  robot: '🤖', book: '📖',
}

interface NodeDef {
  type: string
  label: string
  category: string
  description: string
  icon: string
  color: string
  output_hint?: string
  config?: any[]
}

const RECENT_KEY = 'flowagent_recent_nodes'
const MAX_RECENT = 4

function getRecentTypes(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
  } catch { return [] }
}

function trackRecentNode(type: string) {
  const recent = getRecentTypes().filter(t => t !== type)
  recent.unshift(type)
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)))
}

export default function Sidebar() {
  const [categories, setCategories] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [collapsed, setCollapsed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [recentTypes, setRecentTypes] = useState<string[]>(getRecentTypes())
  const addNode = useWorkflowStore(s => s.addNode)
  const selectNode = useWorkflowStore(s => s.selectNode)

  useEffect(() => {
    setLoading(true)
    fetch('/api/nodes/categories')
      .then(r => r.json())
      .then(setCategories)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const onDragStart = (e: React.DragEvent, node: NodeDef) => {
    e.dataTransfer.setData('application/reactflow', JSON.stringify(node))
    e.dataTransfer.effectAllowed = 'move'
    trackRecentNode(node.type)
    setRecentTypes(getRecentTypes())
  }

  const handleDoubleClick = (nodeDef: NodeDef) => {
    trackRecentNode(nodeDef.type)
    setRecentTypes(getRecentTypes())
    const newNode = {
      id: `${nodeDef.type}_${Date.now()}`,
      type: 'custom' as const,
      position: { x: 250 + Math.random() * 100, y: 150 + Math.random() * 100 },
      data: {
        type: nodeDef.type,
        label: nodeDef.label,
        config: buildDefaultConfig(nodeDef.config || []),
        category: nodeDef.category,
        color: nodeDef.color,
        icon: nodeDef.icon,
      },
    }
    addNode(newNode)
    setTimeout(() => selectNode(newNode.id), 50)
  }

  const filtered = categories.map(cat => ({
    ...cat,
    nodes: cat.nodes.filter((n: NodeDef) =>
      n.label.toLowerCase().includes(search.toLowerCase()) ||
      n.description.toLowerCase().includes(search.toLowerCase())
    ),
  })).filter(cat => cat.nodes.length > 0)

  if (collapsed) {
    return (
      <div className="w-10 bg-[#1e293b] border-r border-[#334155] flex flex-col items-center shrink-0 py-3">
        <button
          onClick={() => setCollapsed(false)}
          className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded-lg transition-colors"
          title="展开节点面板"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    )
  }

  return (
    <div className="w-64 bg-[#1e293b] border-r border-[#334155] flex flex-col shrink-0 overflow-hidden">
      <div className="p-3 border-b border-[#334155] flex items-center gap-2">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="搜索节点..."
            className="w-full pl-9 pr-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-blue-500"
          />
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded-lg transition-colors shrink-0"
          title="收起节点面板"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-32">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2" />
            <p className="text-xs text-[#64748b]">加载节点...</p>
          </div>
        ) : !search && recentTypes.length > 0 && (() => {
          const allNodes = categories.flatMap((c: any) => c.nodes)
          const recentNodes = recentTypes.map(t => allNodes.find((n: NodeDef) => n.type === t)).filter(Boolean)
          if (recentNodes.length === 0) return null
          return (
            <div>
              <h3 className="text-xs font-semibold text-[#64748b] uppercase tracking-wider mb-2 px-1">最近使用</h3>
              <div className="space-y-1">
                {recentNodes.map((node: NodeDef) => (
                  <div
                    key={node.type}
                    draggable
                    onDragStart={e => onDragStart(e, node)}
                    onDoubleClick={() => handleDoubleClick(node)}
                    title={node.output_hint ? `${node.description}\n输出: ${node.output_hint}\n双击添加到画布` : `${node.description}\n双击添加到画布`}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-grab active:cursor-grabbing hover:bg-[#334155] transition-colors group"
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0"
                      style={{ backgroundColor: node.color + '20', color: node.color }}
                    >
                      {ICONS[node.icon] || '●'}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-white truncate">{node.label}</div>
                      <div className="text-xs text-[#64748b] truncate">{node.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })()}
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32">
            <p className="text-xs text-[#64748b]">{search ? '没有匹配的节点' : '暂无节点'}</p>
          </div>
        ) : filtered.map(cat => (
          <div key={cat.id}>
            <h3 className="text-xs font-semibold text-[#64748b] uppercase tracking-wider mb-2 px-1">{cat.label}</h3>
            <div className="space-y-1">
              {cat.nodes.map((node: NodeDef) => (
                <div
                  key={node.type}
                  draggable
                  onDragStart={e => onDragStart(e, node)}
                  onDoubleClick={() => handleDoubleClick(node)}
                  title={node.output_hint ? `${node.description}\n输出: ${node.output_hint}\n双击添加到画布` : `${node.description}\n双击添加到画布`}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-grab active:cursor-grabbing hover:bg-[#334155] transition-colors group"
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0"
                    style={{ backgroundColor: node.color + '20', color: node.color }}
                  >
                    {ICONS[node.icon] || '●'}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">{node.label}</div>
                    <div className="text-xs text-[#64748b] truncate">{node.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="p-3 border-t border-[#334155] text-[10px] text-[#475569] space-y-1">
        <div className="flex justify-between"><span>运行</span><span>Ctrl+Enter</span></div>
        <div className="flex justify-between"><span>保存</span><span>Ctrl+S</span></div>
        <div className="flex justify-between"><span>搜索</span><span>Ctrl+F</span></div>
        <div className="flex justify-between"><span>复制/粘贴</span><span>Ctrl+C/V</span></div>
        <div className="flex justify-between"><span>删除</span><span>Del</span></div>
      </div>
    </div>
  )
}
