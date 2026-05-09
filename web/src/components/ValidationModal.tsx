import { useWorkflowStore } from '../stores/workflowStore'

export default function ValidationModal() {
  const { validationIssues, showValidation, setShowValidation, runWorkflow, selectNode } = useWorkflowStore()

  if (!showValidation || validationIssues.length === 0) return null

  const errors = validationIssues.filter(i => i.level === 'error')
  const warnings = validationIssues.filter(i => i.level === 'warning')

  const handleForceRun = () => {
    // Skip validation and run directly
    setShowValidation(false)
    // Temporarily clear issues and run
    useWorkflowStore.setState({ validationIssues: [] })
    useWorkflowStore.getState().runWorkflow()
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowValidation(false)}>
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl w-[480px] max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="p-4 border-b border-[#334155] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${errors.length > 0 ? 'bg-red-500/20' : 'bg-yellow-500/20'}`}>
              <svg className={`w-5 h-5 ${errors.length > 0 ? 'text-red-400' : 'text-yellow-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm">
                {errors.length > 0 ? '工作流存在问题' : '工作流警告'}
              </h3>
              <p className="text-xs text-[#64748b]">
                {errors.length > 0 ? '请修复以下错误后再运行' : '以下警告可能影响运行结果'}
              </p>
            </div>
          </div>
          <button onClick={() => setShowValidation(false)} className="p-1 hover:bg-[#334155] rounded transition-colors">
            <svg className="w-4 h-4 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Issues list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {errors.map((issue, i) => (
            <div
              key={`e-${i}`}
              className="flex items-start gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg cursor-pointer hover:bg-red-500/15 transition-colors"
              onClick={() => { if (issue.nodeId) { selectNode(issue.nodeId); setShowValidation(false) } }}
            >
              <svg className="w-4 h-4 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              <div>
                <p className="text-sm text-red-300">{issue.message}</p>
                {issue.nodeId && <p className="text-xs text-[#64748b] mt-0.5">点击定位到节点</p>}
              </div>
            </div>
          ))}
          {warnings.map((issue, i) => (
            <div
              key={`w-${i}`}
              className="flex items-start gap-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg cursor-pointer hover:bg-yellow-500/15 transition-colors"
              onClick={() => { if (issue.nodeId) { selectNode(issue.nodeId); setShowValidation(false) } }}
            >
              <svg className="w-4 h-4 text-yellow-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <p className="text-sm text-yellow-300">{issue.message}</p>
                {issue.nodeId && <p className="text-xs text-[#64748b] mt-0.5">点击定位到节点</p>}
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-[#334155] flex justify-end gap-3">
          <button
            onClick={() => setShowValidation(false)}
            className="px-4 py-2 text-sm text-[#94a3b8] hover:text-white transition-colors"
          >
            取消
          </button>
          {warnings.length > 0 && errors.length === 0 && (
            <button
              onClick={handleForceRun}
              className="px-4 py-2 text-sm bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors"
            >
              忽略警告并运行
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
