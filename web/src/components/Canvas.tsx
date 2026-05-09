import { useCallback, useRef, useState, useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useWorkflowStore, type WorkflowNode } from '../stores/workflowStore'
import { buildDefaultConfig } from '../utils/nodeDefaults'
import CustomNode from './nodes/CustomNode'
import CustomEdge from './edges/CustomEdge'
import ContextMenu from './ContextMenu'

const nodeTypes = { custom: CustomNode }
const edgeTypes = { custom: CustomEdge }

export default function Canvas() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition, fitView, zoomIn, zoomOut, setCenter } = useReactFlow()
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, selectNode, selectEdge } = useWorkflowStore()
  const [showMiniMap, setShowMiniMap] = useState(true)
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId?: string } | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Keyboard shortcut for search
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        const target = e.target as HTMLElement
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
        e.preventDefault()
        setShowSearch(true)
        setTimeout(() => searchInputRef.current?.focus(), 50)
      }
      if (e.key === 'Escape' && showSearch) {
        setShowSearch(false)
        setSearchQuery('')
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [showSearch])

  const searchResults = searchQuery.trim()
    ? nodes.filter(n => n.data.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : []

  const handleSearchSelect = (nodeId: string) => {
    selectNode(nodeId)
    const node = nodes.find(n => n.id === nodeId)
    if (node) {
      setCenter(node.position.x + 80, node.position.y + 40, { zoom: 1.5, duration: 300 })
    }
  }

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/reactflow')
    if (!data) return

    const nodeDef = JSON.parse(data)

    const position = screenToFlowPosition({
      x: e.clientX,
      y: e.clientY,
    })

    const newNode: WorkflowNode = {
      id: `${nodeDef.type}_${Date.now()}`,
      type: 'custom',
      position,
      data: {
        type: nodeDef.type,
        label: nodeDef.label,
        config: buildDefaultConfig(nodeDef.config),
        category: nodeDef.category,
        color: nodeDef.color,
        icon: nodeDef.icon,
      },
    }

    addNode(newNode)
    // Auto-select the new node so properties panel opens
    setTimeout(() => selectNode(newNode.id), 50)
  }, [addNode, screenToFlowPosition, selectNode])

  const onNodeClick = useCallback((_: any, node: Node) => {
    selectNode(node.id)
  }, [selectNode])

  const onEdgeClick = useCallback((_: any, edge: any) => {
    selectEdge(edge.id)
  }, [selectEdge])

  const onPaneClick = useCallback(() => {
    selectNode(null)
    setContextMenu(null)
  }, [selectNode])

  const onPaneContextMenu = useCallback((e: React.MouseEvent | MouseEvent) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY })
  }, [])

  const onNodeContextMenu = useCallback((e: React.MouseEvent, node: Node) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY, nodeId: node.id })
  }, [])

  return (
    <div ref={reactFlowWrapper} className="flex-1 h-full relative">
      {/* Empty canvas guide */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="text-center max-w-xs">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#1e293b] border border-[#334155] flex items-center justify-center">
              <svg className="w-8 h-8 text-[#475569]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-[#94a3b8] text-sm mb-1 font-medium">开始构建工作流</p>
            <p className="text-[#64748b] text-xs mb-4">从左侧拖拽节点到此处，或双击快速添加</p>
            <div className="flex flex-col items-center gap-2 pointer-events-auto">
              <button
                onClick={() => {
                  const triggerNode: WorkflowNode = {
                    id: `manual_trigger_${Date.now()}`,
                    type: 'custom',
                    position: { x: 250, y: 150 },
                    data: {
                      type: 'manual_trigger',
                      label: '手动触发',
                      config: {},
                      category: 'trigger',
                      color: '#10b981',
                      icon: 'play',
                    },
                  }
                  addNode(triggerNode)
                  setTimeout(() => selectNode(triggerNode.id), 50)
                }}
                className="px-4 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 hover:border-green-500/50 rounded-lg text-sm text-green-400 hover:text-green-300 transition-all flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                添加触发器节点
              </button>
              <div className="flex flex-wrap justify-center gap-2 mt-1">
                <span className="px-2.5 py-1 bg-[#1e293b] border border-[#334155] rounded-lg text-[10px] text-[#64748b]">Ctrl+Enter 运行</span>
                <span className="px-2.5 py-1 bg-[#1e293b] border border-[#334155] rounded-lg text-[10px] text-[#64748b]">Ctrl+S 保存</span>
                <span className="px-2.5 py-1 bg-[#1e293b] border border-[#334155] rounded-lg text-[10px] text-[#64748b]">Del 删除</span>
              </div>
            </div>
          </div>
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onPaneContextMenu={onPaneContextMenu}
        onNodeContextMenu={onNodeContextMenu}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        snapToGrid
        snapGrid={[16, 16]}
        defaultEdgeOptions={{ type: 'custom', animated: true, style: { stroke: '#64748b', strokeWidth: 2 } }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e293b" />
        <Controls position="bottom-left" />
        {showMiniMap && (
          <MiniMap
            nodeColor={(n) => (n.data as any)?.color || '#3b82f6'}
            maskColor="rgba(15, 23, 42, 0.8)"
            style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          />
        )}
        {/* Node search */}
        {showSearch && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 w-72">
            <div className="bg-[#1e293b] border border-[#334155] rounded-lg shadow-xl overflow-hidden">
              <div className="flex items-center gap-2 px-3 py-2">
                <svg className="w-4 h-4 text-[#64748b] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="搜索节点..."
                  className="flex-1 bg-transparent text-sm text-white placeholder-[#64748b] focus:outline-none"
                  autoFocus
                />
                <span className="text-[10px] text-[#475569]">Esc 关闭</span>
              </div>
              {searchQuery.trim() && (
                <div className="border-t border-[#334155] max-h-48 overflow-y-auto">
                  {searchResults.length === 0 ? (
                    <div className="px-3 py-3 text-xs text-[#64748b] text-center">没有匹配的节点</div>
                  ) : (
                    searchResults.map(n => (
                      <button
                        key={n.id}
                        onClick={() => handleSearchSelect(n.id)}
                        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#334155] transition-colors text-left"
                      >
                        <div
                          className="w-5 h-5 rounded flex items-center justify-center text-[10px] shrink-0"
                          style={{ backgroundColor: n.data.color + '20', color: n.data.color }}
                        >
                          {n.data.label[0]}
                        </div>
                        <span className="text-xs text-white truncate">{n.data.label}</span>
                        <span className="text-[10px] text-[#475569] ml-auto">{n.data.type}</span>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Custom toolbar */}
        <div className="absolute top-3 right-3 flex items-center gap-1 bg-[#1e293b] border border-[#334155] rounded-lg p-1 z-10">
          <button onClick={() => { setShowSearch(!showSearch); if (!showSearch) setTimeout(() => searchInputRef.current?.focus(), 50) }} className={`p-1.5 rounded transition-colors ${showSearch ? 'text-blue-400 bg-blue-500/10' : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155]'}`} title="搜索节点 (Ctrl+F)">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          </button>
          <div className="w-px h-4 bg-[#334155]" />
          <button onClick={() => zoomIn()} className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded transition-colors" title="放大">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          </button>
          <button onClick={() => zoomOut()} className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded transition-colors" title="缩小">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>
          </button>
          <div className="w-px h-4 bg-[#334155]" />
          <button onClick={() => fitView({ padding: 0.2 })} className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded transition-colors" title="适应视图">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
          </button>
          <div className="w-px h-4 bg-[#334155]" />
          <button onClick={() => setShowMiniMap(!showMiniMap)} className={`p-1.5 rounded transition-colors ${showMiniMap ? 'text-blue-400 bg-blue-500/10' : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155]'}`} title="小地图">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>
          </button>
        </div>
      </ReactFlow>
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          nodeId={contextMenu.nodeId}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  )
}
