import { useState, useEffect, useRef, useCallback } from 'react'
import { useWorkflowStore } from '../stores/workflowStore'
import { api } from '../api/client'

const MIN_HEIGHT = 150
const MAX_HEIGHT = 600

export default function BottomPanel() {
  const { bottomTab, setBottomTab, bottomOpen, toggleBottomPanel, execution, currentWorkflowId, nodes, selectNode } = useWorkflowStore()
  const [execHistory, setExecHistory] = useState<any[]>([])
  const [selectedExec, setSelectedExec] = useState<any>(null)
  const [collapsedOutputs, setCollapsedOutputs] = useState<Record<string, boolean>>({})
  const [panelHeight, setPanelHeight] = useState(208)
  const [isResizing, setIsResizing] = useState(false)
  const logEndRef = useRef<HTMLDivElement>(null)

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    const startY = e.clientY
    const startHeight = panelHeight

    const handleMouseMove = (e: MouseEvent) => {
      const delta = startY - e.clientY
      const newHeight = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, startHeight + delta))
      setPanelHeight(newHeight)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [panelHeight])

  // Auto-scroll logs
  useEffect(() => {
    if (bottomTab === 'logs' && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [execution?.logs?.length, bottomTab])

  useEffect(() => {
    if (bottomTab === 'history' && currentWorkflowId) {
      api.listExecutions(currentWorkflowId).then(setExecHistory).catch(() => {})
    }
  }, [bottomTab, currentWorkflowId])

  if (!bottomOpen) return null

  const logs = execution?.logs || []
  const results = execution?.results || {}
  const errors = logs.filter((l: any) => l.level === 'error')

  // Build node label map for friendly display
  const nodeLabelMap: Record<string, string> = {}
  nodes.forEach(n => { nodeLabelMap[n.id] = n.data.label })

  const getNodeLabel = (nodeId: string) => nodeLabelMap[nodeId] || nodeId

  const renderLogs = (logList: any[], emptyText: string) => (
    logList.length === 0 ? (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <svg className="w-8 h-8 text-[#334155] mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-[#475569] text-xs">{emptyText}</p>
      </div>
    ) : (
      <div className="space-y-0.5">
        {logList.map((log: any, i: number) => (
          <div key={i} className={`flex items-start gap-2 py-0.5 px-1 rounded hover:bg-[#0f172a] ${
            log.level === 'error' ? 'text-red-400' :
            log.level === 'success' ? 'text-green-400' :
            log.level === 'warning' ? 'text-yellow-400' : 'text-[#94a3b8]'
          }`}>
            <span className="text-[#334155] shrink-0 w-16">{log.time?.split('T')[1]?.split('.')[0] || ''}</span>
            {log.node && (
              <button
                onClick={() => selectNode(log.node)}
                className="text-blue-400 hover:text-blue-300 hover:underline shrink-0 max-w-[120px] truncate text-left"
                title={`点击定位到 ${getNodeLabel(log.node)}`}
              >
                {getNodeLabel(log.node)}
              </button>
            )}
            <span className="flex-1 min-w-0 break-all">{log.message}</span>
          </div>
        ))}
        <div ref={logEndRef} />
      </div>
    )
  )

  return (
    <div
      className="bg-[#1e293b] border-t border-[#334155] flex flex-col shrink-0 animate-slide-in"
      style={{ height: panelHeight }}
    >
      {/* Resize handle */}
      <div
        onMouseDown={handleResizeStart}
        className={`h-1.5 cursor-row-resize flex items-center justify-center hover:bg-blue-500/30 transition-colors ${isResizing ? 'bg-blue-500/30' : ''}`}
      >
        <div className="w-8 h-0.5 rounded-full bg-[#334155]" />
      </div>
      {/* Tabs */}
      <div className="flex items-center border-b border-[#334155] px-3 shrink-0">
        <TabButton active={bottomTab === 'logs'} onClick={() => setBottomTab('logs')} color="blue" label="日志" count={logs.length} />
        <TabButton active={bottomTab === 'output'} onClick={() => setBottomTab('output')} color="blue" label="输出" count={Object.keys(results).length} />
        <TabButton active={bottomTab === 'errors'} onClick={() => setBottomTab('errors')} color="red" label="错误" count={errors.length} />
        <TabButton active={bottomTab === 'history'} onClick={() => setBottomTab('history')} color="purple" label="历史" />
        <div className="flex-1" />
        <button onClick={toggleBottomPanel} className="p-1 hover:bg-[#334155] rounded transition-colors" title="关闭面板">
          <svg className="w-3.5 h-3.5 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs">
        {bottomTab === 'logs' && renderLogs(logs, '运行工作流查看日志')}
        {bottomTab === 'errors' && renderLogs(errors, '没有错误')}

        {bottomTab === 'output' && (
          Object.keys(results).length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <svg className="w-8 h-8 text-[#334155] mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <p className="text-[#475569] text-xs">运行工作流查看输出</p>
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(results).map(([nodeId, result]: [string, any]) => {
                const nodeStatus = execution?.nodeStatuses?.[nodeId]
                const hasError = nodeStatus === 'failed' || (result && result.error)
                const isCollapsed = collapsedOutputs[nodeId]
                const resultStr = typeof result === 'string' ? result : JSON.stringify(result, null, 2)
                const isLong = resultStr.length > 300
                return (
                  <div key={nodeId} className={`bg-[#0f172a] rounded-lg border ${hasError ? 'border-red-500/30' : 'border-[#334155]'} p-2.5`}>
                    <div className="flex items-center gap-2 mb-1.5">
                      {hasError ? (
                        <svg className="w-3.5 h-3.5 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5 text-green-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                      <button
                        onClick={() => selectNode(nodeId)}
                        className="text-blue-400 hover:text-blue-300 hover:underline text-xs font-medium"
                      >
                        {getNodeLabel(nodeId)}
                      </button>
                      {isLong && (
                        <button
                          onClick={() => setCollapsedOutputs(prev => ({ ...prev, [nodeId]: !prev[nodeId] }))}
                          className="ml-auto text-[#475569] hover:text-[#64748b] text-[10px]"
                        >
                          {isCollapsed ? '展开' : '收起'}
                        </button>
                      )}
                    </div>
                    <pre className={`text-[#94a3b8] text-[11px] whitespace-pre-wrap break-all ${isLong && isCollapsed ? 'max-h-16' : 'max-h-40'} overflow-y-auto`}>
                      {isLong && isCollapsed ? resultStr.slice(0, 200) + '...' : resultStr}
                    </pre>
                  </div>
                )
              })}
            </div>
          )
        )}

        {bottomTab === 'history' && (
          selectedExec ? (
            <div>
              <button onClick={() => setSelectedExec(null)} className="text-blue-400 hover:text-blue-300 text-xs mb-2 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                返回列表
              </button>
              <div className="flex items-center gap-3 mb-3 text-xs">
                <span className={`px-2 py-0.5 rounded font-medium ${
                  selectedExec.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  selectedExec.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                  'bg-yellow-500/20 text-yellow-400'
                }`}>{selectedExec.status}</span>
                <span className="text-[#64748b]">{new Date(selectedExec.started_at).toLocaleString('zh-CN')}</span>
              </div>
              <div className="space-y-0.5">
                {(selectedExec.logs || []).map((log: any, i: number) => (
                  <div key={i} className={`flex items-start gap-2 py-0.5 px-1 rounded hover:bg-[#0f172a] ${
                    log.level === 'error' ? 'text-red-400' :
                    log.level === 'success' ? 'text-green-400' :
                    log.level === 'warning' ? 'text-yellow-400' : 'text-[#94a3b8]'
                  }`}>
                    <span className="text-[#334155] shrink-0 w-16">{log.time?.split('T')[1]?.split('.')[0] || ''}</span>
                    {log.node && <span className="text-[#64748b] shrink-0 max-w-[100px] truncate">{getNodeLabel(log.node)}</span>}
                    <span className="flex-1 min-w-0 break-all">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            execHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <svg className="w-8 h-8 text-[#334155] mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-[#475569] text-xs">暂无执行历史</p>
              </div>
            ) : (
              <div className="space-y-1">
                {execHistory.map((exec: any) => (
                  <div
                    key={exec.id}
                    onClick={async () => {
                      const detail = await api.getExecution(exec.id)
                      setSelectedExec(detail)
                    }}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#0f172a] cursor-pointer transition-colors border border-transparent hover:border-[#334155]"
                  >
                    <div className={`w-2 h-2 rounded-full shrink-0 ${
                      exec.status === 'completed' ? 'bg-green-500' :
                      exec.status === 'failed' ? 'bg-red-500' :
                      exec.status === 'running' ? 'bg-yellow-500 animate-pulse' : 'bg-[#475569]'
                    }`} />
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      exec.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      exec.status === 'failed' ? 'bg-red-500/20 text-red-400' : 'bg-[#334155] text-[#64748b]'
                    }`}>{exec.status}</span>
                    {exec.duration_ms !== null && (
                      <span className="text-xs text-[#64748b]">{exec.duration_ms}ms</span>
                    )}
                    <span className="text-xs text-[#64748b]">{exec.node_count} 节点</span>
                    {exec.failed_nodes > 0 && (
                      <span className="text-xs text-red-400">{exec.failed_nodes} 失败</span>
                    )}
                    <span className="text-xs text-[#475569] ml-auto">{new Date(exec.started_at).toLocaleString('zh-CN')}</span>
                  </div>
                ))}
              </div>
            )
          )
        )}
      </div>
    </div>
  )
}

function TabButton({ active, onClick, color, label, count }: {
  active: boolean; onClick: () => void; color: string; label: string; count?: number
}) {
  const colorClasses: Record<string, string> = {
    blue: 'border-blue-500 text-blue-400',
    red: 'border-red-500 text-red-400',
    purple: 'border-purple-500 text-purple-400',
  }
  return (
    <button
      onClick={onClick}
      className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
        active ? colorClasses[color] : 'border-transparent text-[#64748b] hover:text-[#94a3b8]'
      }`}
    >
      {label}{count !== undefined && ` (${count})`}
    </button>
  )
}
