import { useEffect, useCallback, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useWorkflowStore } from '../stores/workflowStore'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import Canvas from '../components/Canvas'
import PropertiesPanel from '../components/PropertiesPanel'
import BottomPanel from '../components/BottomPanel'
import ValidationModal from '../components/ValidationModal'
import ToastContainer, { showToast } from '../components/Toast'

export default function Editor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { loadWorkflow, currentWorkflowId, toggleBottomPanel, bottomOpen, execution, selectedNodeId, selectedEdgeId, removeNode, removeEdge, saveWorkflow, undo, redo, runWorkflow, isRunning, copyNode, pasteNodes, loadError } = useWorkflowStore()
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [autoSaving, setAutoSaving] = useState(false)

  useEffect(() => {
    if (id && id !== currentWorkflowId) {
      loadWorkflow(id)
    }
  }, [id])

  // Auto-save every 30 seconds (only if dirty)
  useEffect(() => {
    if (!currentWorkflowId) return
    const interval = setInterval(async () => {
      if (!useWorkflowStore.getState().isDirty) return
      setAutoSaving(true)
      try {
        await saveWorkflow()
        setLastSaved(new Date())
      } catch {}
      setAutoSaving(false)
    }, 30000)
    return () => clearInterval(interval)
  }, [currentWorkflowId, saveWorkflow])

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Delete selected node or edge
    if (e.key === 'Delete' || e.key === 'Backspace') {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return
      e.preventDefault()
      if (selectedNodeId) removeNode(selectedNodeId)
      else if (selectedEdgeId) removeEdge(selectedEdgeId)
    }
    // Ctrl+Enter to run workflow
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (!isRunning) runWorkflow()
    }
    // Ctrl+S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      saveWorkflow()
    }
    // Ctrl+Z to undo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return
      e.preventDefault()
      undo()
    }
    // Ctrl+Shift+Z to redo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return
      e.preventDefault()
      redo()
    }
    // Ctrl+C to copy selected node
    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return
      if (selectedNodeId) {
        e.preventDefault()
        copyNode(selectedNodeId)
      }
    }
    // Ctrl+V to paste
    if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return
      e.preventDefault()
      pasteNodes()
    }
    // Escape to deselect
    if (e.key === 'Escape') {
      useWorkflowStore.getState().selectNode(null)
    }
  }, [selectedNodeId, selectedEdgeId, removeNode, removeEdge, saveWorkflow, undo, redo, isRunning, runWorkflow, copyNode, pasteNodes])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  const status = execution?.status

  const handleManualSave = async () => {
    await saveWorkflow()
    setLastSaved(new Date())
    showToast('工作流已保存', 'success')
  }

  // Watch execution status for toast notifications and auto-switch tab
  useEffect(() => {
    if (execution?.status === 'completed') {
      showToast('工作流执行完成', 'success')
      useWorkflowStore.getState().setBottomTab('output')
    } else if (execution?.status === 'failed') {
      showToast('工作流执行失败', 'error')
      useWorkflowStore.getState().setBottomTab('errors')
    }
  }, [execution?.status])

  if (loadError) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-[#0f172a]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-red-500/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-white mb-2">加载失败</h2>
          <p className="text-sm text-[#94a3b8] mb-6">{loadError}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            返回首页
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 flex overflow-hidden">
            <Canvas />
            <PropertiesPanel />
          </div>
          {/* Bottom panel toggle */}
          {!bottomOpen && (
            <button
              onClick={toggleBottomPanel}
              className="h-8 bg-[#1e293b] border-t border-[#334155] flex items-center justify-center gap-2 text-xs text-[#64748b] hover:text-[#94a3b8] transition-colors shrink-0"
            >
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
              输出面板
              {status && (
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
                  status === 'failed' ? 'bg-red-500/20 text-red-400' : 'bg-[#334155] text-[#64748b]'
                }`}>
                  {status}
                </span>
              )}
              <span className="ml-auto flex items-center gap-1.5">
                {autoSaving && <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />}
                {lastSaved && (
                  <span className="text-[#475569]">
                    {autoSaving ? '保存中...' : `已保存 ${lastSaved.toLocaleTimeString('zh-CN')}`}
                  </span>
                )}
              </span>
            </button>
          )}
          <BottomPanel />
        </div>
      </div>
      <ValidationModal />
      <ToastContainer />
    </div>
  )
}
