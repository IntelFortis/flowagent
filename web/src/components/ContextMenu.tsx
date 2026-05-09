import { useEffect, useRef } from 'react'
import { useReactFlow } from '@xyflow/react'
import { useWorkflowStore, type WorkflowNode } from '../stores/workflowStore'

interface ContextMenuProps {
  x: number
  y: number
  nodeId?: string
  onClose: () => void
}

export default function ContextMenu({ x, y, nodeId, onClose }: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null)
  const { removeNode, selectNode, nodes, edges, addNode, autoLayout, clearCanvas, copyNode, pasteNodes, canPaste } = useWorkflowStore()
  const { fitView, setCenter } = useReactFlow()

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [onClose])

  const handleCopy = () => {
    if (nodeId) copyNode(nodeId)
    onClose()
  }

  const handlePaste = () => {
    pasteNodes()
    onClose()
  }

  const handleDuplicate = () => {
    if (!nodeId) return
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return
    const newNode: WorkflowNode = {
      ...node,
      id: `${node.data.type}_${Date.now()}`,
      position: { x: node.position.x + 40, y: node.position.y + 40 },
      data: { ...node.data },
    }
    addNode(newNode)
    onClose()
  }

  const handleDelete = () => {
    if (nodeId) removeNode(nodeId)
    onClose()
  }

  const handleDisconnect = () => {
    if (!nodeId) return
    useWorkflowStore.setState({
      edges: edges.filter(e => e.source !== nodeId && e.target !== nodeId),
    })
    onClose()
  }

  const handleSelectAll = () => {
    // Select all is handled by React Flow internally
    onClose()
  }

  const handleAutoLayout = () => {
    autoLayout('LR')
    onClose()
  }

  const handleFitView = () => {
    fitView({ padding: 0.2, duration: 300 })
    onClose()
  }

  const handleClearCanvas = () => {
    if (confirm('确定清空画布？此操作可撤销。')) clearCanvas()
    onClose()
  }

  // Adjust position to stay within viewport
  const menuStyle: React.CSSProperties = {
    position: 'fixed',
    left: Math.min(x, window.innerWidth - 200),
    top: Math.min(y, window.innerHeight - 300),
  }

  if (nodeId) {
    // Node context menu
    return (
      <div ref={ref} style={menuStyle} className="bg-[#1e293b] border border-[#334155] rounded-lg shadow-xl py-1 w-48 z-50">
        <MenuItem icon="copy" label="复制" shortcut="Ctrl+C" onClick={handleCopy} />
        <MenuItem icon="duplicate" label="快速复制" shortcut="偏移复制" onClick={handleDuplicate} />
        <MenuItem icon="fitView" label="定位到节点" onClick={() => {
          const node = nodes.find(n => n.id === nodeId)
          if (node) {
            setCenter(node.position.x + 80, node.position.y + 40, { zoom: 1.5, duration: 300 })
            selectNode(nodeId!)
          }
          onClose()
        }} />
        <MenuItem icon="disconnect" label="断开连接" onClick={handleDisconnect} />
        <div className="h-px bg-[#334155] my-1" />
        <MenuItem icon="delete" label="删除" shortcut="Del" onClick={handleDelete} danger />
      </div>
    )
  }

  // Canvas context menu
  return (
    <div ref={ref} style={menuStyle} className="bg-[#1e293b] border border-[#334155] rounded-lg shadow-xl py-1 w-48 z-50">
      {canPaste() && <MenuItem icon="paste" label="粘贴" shortcut="Ctrl+V" onClick={handlePaste} />}
      <MenuItem icon="layout" label="自动排列" onClick={handleAutoLayout} />
      <MenuItem icon="fitView" label="适应视图" onClick={handleFitView} />
      <div className="h-px bg-[#334155] my-1" />
      <MenuItem icon="clear" label="清空画布" onClick={handleClearCanvas} danger />
    </div>
  )
}

function MenuItem({ icon, label, shortcut, onClick, danger }: {
  icon: string
  label: string
  shortcut?: string
  onClick: () => void
  danger?: boolean
}) {
  const icons: Record<string, JSX.Element> = {
    copy: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
    paste: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
    duplicate: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
    disconnect: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>,
    delete: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
    layout: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>,
    fitView: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>,
    clear: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
  }

  return (
    <button
      onClick={onClick}
      className={`w-full px-3 py-2 text-sm flex items-center gap-2 transition-colors ${
        danger ? 'text-red-400 hover:bg-red-500/10' : 'text-[#94a3b8] hover:bg-[#334155] hover:text-white'
      }`}
    >
      {icons[icon]}
      <span className="flex-1 text-left">{label}</span>
      {shortcut && <span className="text-[10px] text-[#475569]">{shortcut}</span>}
    </button>
  )
}
