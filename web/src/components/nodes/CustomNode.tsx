import { useState, useRef, useEffect } from 'react'
import { Handle, Position } from '@xyflow/react'
import { useWorkflowStore } from '../../stores/workflowStore'

const ICONS: Record<string, string> = {
  play: '▶', webhook: '🔗', clock: '🕐', globe: '🌐', braces: '{ }',
  filter: '▼', shuffle: '⇄', variable: 'x=', brain: '🧠', 'file-text': '📄',
  languages: '🌐', tags: '🏷', 'git-branch': '⑂', timer: '⏱', repeat: '↻',
  code: '</>', mail: '✉', send: '→', download: '⬇', terminal: '>',
  table: '⊞', link: '⊶', scissors: '✂', 'bar-chart': '▮',
  robot: '🤖', book: '📖',
}

const STATUS_STYLES: Record<string, { border: string; glow: string; badge: string; label: string }> = {
  pending: { border: 'border-[#334155]', glow: '', badge: 'bg-[#475569]', label: '' },
  running: { border: 'border-yellow-500', glow: 'shadow-lg shadow-yellow-500/30 animate-pulse', badge: 'bg-yellow-500', label: '运行中' },
  completed: { border: 'border-green-500', glow: '', badge: 'bg-green-500', label: '完成' },
  failed: { border: 'border-red-500', glow: 'shadow-lg shadow-red-500/20', badge: 'bg-red-500', label: '失败' },
  skipped: { border: 'border-[#475569]', glow: '', badge: 'bg-[#475569]', label: '跳过' },
}

export default function CustomNode({ id, data, selected }: { id: string; data: any; selected?: boolean }) {
  const selectNode = useWorkflowStore((s: any) => s.selectNode)
  const removeNode = useWorkflowStore((s: any) => s.removeNode)
  const edges = useWorkflowStore((s: any) => s.edges)
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const status = data.status || 'pending'
  const st = STATUS_STYLES[status] || STATUS_STYLES.pending

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditValue(data.label)
    setEditing(true)
  }

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editing])

  const commitEdit = () => {
    if (editValue.trim()) {
      useWorkflowStore.getState().updateNodeConfig(id, { __label: editValue.trim() })
      // Update label directly via nodes
      useWorkflowStore.setState({
        nodes: useWorkflowStore.getState().nodes.map(n =>
          n.id === id ? { ...n, data: { ...n.data, label: editValue.trim() } } : n
        ),
      })
    }
    setEditing(false)
  }

  const hasInput = data.category !== 'trigger'
  const hasOutput = data.category !== 'output'
  const isCondition = data.type === 'condition'
  const hasIncomingEdge = edges.some((e: any) => e.target === id)
  const showInputHint = hasInput && !hasIncomingEdge

  return (
    <div
      className={`group min-w-[160px] rounded-xl border-2 transition-all cursor-pointer ${
        selected ? 'border-blue-500 shadow-lg shadow-blue-500/20' : `${st.border} ${st.glow} hover:border-[#475569]`
      }`}
      style={{ background: '#1e293b' }}
      onClick={() => selectNode(id)}
    >
      {/* Input Handle */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Left}
          className={`!w-3 !h-3 !border-2 !border-[#1e293b] hover:!bg-blue-500 !-left-[6px] ${showInputHint ? '!bg-blue-500/50 !animate-pulse' : '!bg-[#475569]'}`}
          title="输入：接收上游节点的输出数据"
        />
      )}

      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2.5 rounded-t-[10px]"
        style={{ background: data.color + '15' }}
      >
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs shrink-0"
          style={{ backgroundColor: data.color + '30', color: data.color }}
        >
          {status === 'running' ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : status === 'completed' ? (
            <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : status === 'failed' ? (
            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            ICONS[data.icon] || '●'
          )}
        </div>
        {editing ? (
          <input
            ref={inputRef}
            value={editValue}
            onChange={e => setEditValue(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={e => { e.stopPropagation(); if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(false) }}
            onClick={e => e.stopPropagation()}
            className="flex-1 min-w-0 bg-[#0f172a] border border-blue-500 rounded px-1.5 py-0.5 text-sm text-white focus:outline-none"
          />
        ) : (
          <span className="text-sm font-medium text-white truncate flex-1 cursor-text" onDoubleClick={handleDoubleClick} title="双击重命名">{data.label}</span>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); removeNode(id); }}
          className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-red-500/20 rounded transition-all"
          title="删除节点"
        >
          <svg className="w-3.5 h-3.5 text-[#64748b] hover:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Body */}
      <div className="px-3 py-2 text-xs text-[#94a3b8]">
        <div className="flex items-center gap-1.5">
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={{ background: data.color + '20', color: data.color }}
          >
            {data.category}
          </span>
          {data.config && Object.keys(data.config).length > 0 && (
            <span className="text-[#64748b]">{Object.keys(data.config).length} 个参数</span>
          )}
          {st.label && (
            <span className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-medium ${
              status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
              status === 'completed' ? 'bg-green-500/20 text-green-400' :
              status === 'failed' ? 'bg-red-500/20 text-red-400' :
              'bg-[#334155] text-[#64748b]'
            }`}>
              {st.label}
            </span>
          )}
        </div>
        {showInputHint && (
          <div className="mt-1.5 text-[10px] text-blue-400/60 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            从上游节点拖线连接
          </div>
        )}
      </div>

      {/* Running progress bar */}
      {status === 'running' && (
        <div className="h-0.5 bg-yellow-500/20 rounded-b-xl overflow-hidden">
          <div className="h-full bg-yellow-500 rounded-b-xl animate-progress" style={{ width: '60%' }} />
        </div>
      )}

      {/* Output Handle */}
      {hasOutput && !isCondition && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-[#475569] !border-2 !border-[#1e293b] hover:!bg-blue-500 !-right-[6px]"
          title="输出：传递数据到下游节点"
        />
      )}
      {isCondition && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            className="!w-3 !h-3 !bg-green-500 !border-2 !border-[#1e293b] hover:!bg-green-400 !-right-[6px]"
            style={{ top: '35%' }}
            title="是 (True)：条件成立时走此分支"
          />
          <Handle
            type="source"
            position={Position.Right}
            id="false"
            className="!w-3 !h-3 !bg-red-500 !border-2 !border-[#1e293b] hover:!bg-red-400 !-right-[6px]"
            style={{ top: '65%' }}
            title="否 (False)：条件不成立时走此分支"
          />
        </>
      )}
    </div>
  )
}
