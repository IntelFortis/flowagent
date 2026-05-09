import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkflowStore } from '../stores/workflowStore'
import { api } from '../api/client'
import { showToast } from './Toast'
import SettingsModal from './SettingsModal'

export default function Navbar() {
  const navigate = useNavigate()
  const { workflowName, setWorkflowName, workflowDescription, setWorkflowDescription, saveWorkflow, runWorkflow, stopWorkflow, isRunning, nodes, edges, loadWorkflow, createWorkflow, autoLayout, undo, redo, canUndo, canRedo, execution, isDirty } = useWorkflowStore()
  const importRef = useRef<HTMLInputElement>(null)
  const [showSettings, setShowSettings] = useState(false)

  const handleExport = () => {
    const data = {
      name: workflowName,
      nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges,
      exportedAt: new Date().toISOString(),
      version: '1.0',
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${workflowName || 'workflow'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = async (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string)
        if (data.nodes && data.edges) {
          const id = await createWorkflow(data.name || '导入的工作流')
          await api.updateWorkflow(id, { name: data.name, nodes: data.nodes, edges: data.edges })
          await loadWorkflow(id)
          showToast('工作流导入成功', 'success')
          navigate(`/editor/${id}`)
        } else {
          showToast('导入失败: 文件格式不正确', 'error')
        }
      } catch (err) {
        showToast('导入失败: 无效的 JSON 文件', 'error')
      }
    }
    reader.readAsText(file)
    if (importRef.current) importRef.current.value = ''
  }

  return (
    <>
    <header className="h-14 bg-[#1e293b] border-b border-[#334155] flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="font-bold text-white text-sm">FlowAgent</span>
        </button>
        <div className="w-px h-6 bg-[#334155]" />
        <div className="flex flex-col">
          <div className="flex items-center">
            <input
              type="text"
              value={workflowName}
              onChange={e => setWorkflowName(e.target.value)}
              className="bg-transparent text-white font-medium text-sm border-none outline-none focus:bg-[#0f172a] px-2 py-0.5 rounded w-56"
            />
            {isDirty && (
              <span className="w-2 h-2 rounded-full bg-orange-400 shrink-0" title="有未保存的更改" />
            )}
          </div>
          <input
            type="text"
            value={workflowDescription}
            onChange={e => setWorkflowDescription(e.target.value)}
            placeholder="添加描述..."
            className="bg-transparent text-[#64748b] text-xs border-none outline-none focus:bg-[#0f172a] px-2 py-0.5 rounded w-56 placeholder-[#334155]"
          />
        </div>
        {nodes.length > 0 && (
          <span className="text-[10px] text-[#475569] bg-[#0f172a] px-2 py-0.5 rounded-full">{nodes.length} 节点</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Undo */}
        <button
          onClick={undo}
          disabled={!canUndo()}
          className={`p-1.5 rounded-lg transition-colors ${canUndo() ? 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155]' : 'text-[#334155] cursor-not-allowed'}`}
          title="撤销 (Ctrl+Z)"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
          </svg>
        </button>
        {/* Redo */}
        <button
          onClick={redo}
          disabled={!canRedo()}
          className={`p-1.5 rounded-lg transition-colors ${canRedo() ? 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155]' : 'text-[#334155] cursor-not-allowed'}`}
          title="重做 (Ctrl+Shift+Z)"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10H11a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6" />
          </svg>
        </button>
        {/* Auto Layout */}
        <button
          onClick={() => autoLayout('LR')}
          className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded-lg transition-colors"
          title="自动排列节点"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
        </button>
        {/* Export */}
        <button
          onClick={handleExport}
          className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded-lg transition-colors"
          title="导出工作流"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>
        {/* Import */}
        <button
          onClick={() => importRef.current?.click()}
          className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded-lg transition-colors"
          title="导入工作流"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </button>
        <input ref={importRef} type="file" accept=".json" onChange={handleImport} className="hidden" />

        <div className="w-px h-6 bg-[#334155]" />

        {/* Settings */}
        <button
          onClick={() => setShowSettings(true)}
          className="p-1.5 text-[#64748b] hover:text-[#94a3b8] hover:bg-[#334155] rounded-lg transition-colors"
          title="模型设置"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>

        <button
          onClick={async () => { await saveWorkflow(); showToast('已保存', 'success') }}
          className={`px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-1.5 ${
            isDirty
              ? 'text-orange-300 hover:text-white border border-orange-500/50 hover:border-orange-400 bg-orange-500/10'
              : 'text-[#94a3b8] hover:text-white border border-[#334155] hover:border-[#475569]'
          }`}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          保存
        </button>

        {isRunning ? (
          <button
            onClick={stopWorkflow}
            className="px-4 py-1.5 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
            停止
          </button>
        ) : (
          <button
            onClick={runWorkflow}
            className="px-4 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            运行
          </button>
        )}
      </div>
    </header>
    {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  )
}
