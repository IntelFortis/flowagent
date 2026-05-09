import { useState, useRef, useEffect } from 'react'
import { useWorkflowStore } from '../stores/workflowStore'
import { getSettings } from './SettingsModal'

export default function PropertiesPanel() {
  const { selectedNodeId, nodes, edges, updateNodeConfig, removeNode } = useWorkflowStore()
  const node = nodes.find(n => n.id === selectedNodeId)
  const [focusedField, setFocusedField] = useState<string | null>(null)

  if (!node) {
    return (
      <div className="w-80 bg-[#1e293b] border-l border-[#334155] flex flex-col shrink-0 overflow-hidden">
        <div className="p-4 border-b border-[#334155]">
          <h3 className="font-semibold text-white text-sm mb-1">快速开始</h3>
          <p className="text-xs text-[#64748b]">4 步构建你的工作流</p>
        </div>
        <div className="p-4 space-y-3 flex-1">
          <QuickStep num={1} title="拖拽节点" desc="从左侧面板拖拽节点到画布，或双击快速添加" icon="drag" />
          <QuickStep num={2} title="连接节点" desc="从一个节点的输出端拖线到另一个的输入端" icon="connect" />
          <QuickStep num={3} title="配置参数" desc="点击节点设置 URL、提示词等参数" icon="config" />
          <QuickStep num={4} title="运行工作流" desc="点击右上角「运行」或按 Ctrl+Enter" icon="run" />
        </div>
        <div className="p-4 border-t border-[#334155] text-[10px] text-[#475569] space-y-1">
          <div className="flex justify-between"><span>运行</span><span>Ctrl+Enter</span></div>
          <div className="flex justify-between"><span>保存</span><span>Ctrl+S</span></div>
          <div className="flex justify-between"><span>撤销</span><span>Ctrl+Z</span></div>
          <div className="flex justify-between"><span>删除</span><span>Del</span></div>
        </div>
      </div>
    )
  }

  function QuickStep({ num, title, desc, icon }: { num: number; title: string; desc: string; icon: string }) {
    const icons: Record<string, JSX.Element> = {
      drag: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>,
      connect: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>,
      config: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
      run: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    }
    return (
      <div className="flex items-start gap-3">
        <div className="w-7 h-7 rounded-lg bg-blue-500/15 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
          {icons[icon]}
        </div>
        <div>
          <p className="text-sm text-white font-medium">{title}</p>
          <p className="text-xs text-[#64748b] mt-0.5">{desc}</p>
        </div>
      </div>
    )
  }

  const handleConfigChange = (key: string, value: any) => {
    updateNodeConfig(node.id, { [key]: value })
  }

  const insertVariable = (varText: string) => {
    if (!focusedField) return
    const current = node.data.config[focusedField] || ''
    handleConfigChange(focusedField, current + varText)
  }

  // Find upstream nodes for variable references
  const upstreamNodeIds = edges.filter(e => e.target === node.id).map(e => e.source)
  const upstreamNodes = nodes.filter(n => upstreamNodeIds.includes(n.id))

  // Fetch node definition for config fields
  const configFields = getNodeConfigFields(node.data.type)

  return (
    <div className="w-80 bg-[#1e293b] border-l border-[#334155] flex flex-col shrink-0 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[#334155]">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-white text-sm">{node.data.label}</h3>
          <button
            onClick={() => removeNode(node.id)}
            className="p-1 hover:bg-[#334155] rounded transition-colors"
            title="删除节点"
          >
            <svg className="w-4 h-4 text-[#64748b] hover:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
        <span
          className="px-2 py-0.5 rounded text-xs font-medium"
          style={{ background: node.data.color + '20', color: node.data.color }}
        >
          {node.data.category}
        </span>
        {getNodeOutputHint(node.data.type) && (
          <div className="mt-2 px-2 py-1.5 bg-[#0f172a] rounded text-[10px] text-[#64748b] font-mono">
            <span className="text-[#475569]">输出: </span>{getNodeOutputHint(node.data.type)}
          </div>
        )}
      </div>

      {/* Demo mode banner for AI nodes */}
      {isAiNode(node.data.type) && !node.data.config.api_key && !getSettings().api_key && (
        <div className="px-4 py-2.5 bg-yellow-500/10 border-b border-yellow-500/20">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-xs text-yellow-300 font-medium">演示模式</p>
              <p className="text-[10px] text-yellow-400/70 mt-0.5">
                未配置 API Key，将返回模拟数据。
                <button onClick={() => document.querySelector<HTMLButtonElement>('[title="模型设置"]')?.click()} className="underline hover:text-yellow-300 ml-1">
                  点击配置
                </button>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Variable Picker */}
      {upstreamNodes.length > 0 && (
        <div className="border-b border-[#334155] px-4 py-2.5">
          <div className="flex items-center gap-1.5 text-xs text-blue-400 mb-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            可引用的数据
          </div>
          <div className="space-y-1">
            {upstreamNodes.map(upNode => (
              <button
                key={upNode.id}
                onClick={() => insertVariable(`{{${upNode.data.label}.output}}`)}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg bg-[#0f172a] hover:bg-blue-500/10 border border-[#334155] hover:border-blue-500/30 transition-all text-left group"
              >
                <div
                  className="w-5 h-5 rounded flex items-center justify-center text-[10px] shrink-0"
                  style={{ backgroundColor: upNode.data.color + '20', color: upNode.data.color }}
                >
                  {upNode.data.label[0]}
                </div>
                <div className="min-w-0 flex-1">
                  <span className="text-xs text-white truncate block">{upNode.data.label}</span>
                </div>
                <code className="text-[10px] text-green-400 shrink-0">
                  {`{{${upNode.data.label}.output}}`}
                </code>
              </button>
            ))}
          </div>
          <p className="text-[10px] text-[#475569] mt-1.5">
            {focusedField ? `点击变量插入到「${focusedField}」` : '先点击输入框，再点击变量'}
          </p>
        </div>
      )}

      {/* Config Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {configFields.length === 0 && (
          <div className="text-center py-8">
            <p className="text-xs text-[#94a3b8] mb-1">此节点无需配置</p>
            <p className="text-[10px] text-[#64748b]">连接到下游节点即可传递数据</p>
          </div>
        )}

        {configFields.map(field => (
          <div key={field.key}>
            <label className="block text-xs font-medium text-[#94a3b8] mb-1.5">
              {field.label}
              {field.required && <span className="text-red-400 ml-0.5">*</span>}
            </label>
            {field.type === 'textarea' ? (
              <div className="relative">
                <textarea
                  value={node.data.config[field.key] || field.default || ''}
                  onChange={e => handleConfigChange(field.key, e.target.value)}
                  onFocus={() => setFocusedField(field.key)}
                  rows={field.key === 'code' ? 6 : 3}
                  placeholder={field.placeholder}
                  className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#475569] focus:outline-none focus:border-blue-500 resize-none font-mono text-xs"
                />
                {upstreamNodes.length > 0 && (
                  <button
                    onClick={() => setFocusedField(field.key)}
                    className="absolute top-2 right-2 p-1 text-[#475569] hover:text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
                    title="插入变量"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </button>
                )}
              </div>
            ) : field.type === 'select' ? (
              <select
                value={node.data.config[field.key] || field.default || ''}
                onChange={e => handleConfigChange(field.key, e.target.value)}
                className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
              >
                {(field.options || []).map((opt: string) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            ) : field.type === 'number' ? (
              <input
                type="number"
                value={node.data.config[field.key] ?? field.default ?? ''}
                onChange={e => handleConfigChange(field.key, Number(e.target.value))}
                placeholder={field.placeholder}
                className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#475569] focus:outline-none focus:border-blue-500"
              />
            ) : (
              <div className="relative">
                <input
                  type="text"
                  value={node.data.config[field.key] || field.default || ''}
                  onChange={e => handleConfigChange(field.key, e.target.value)}
                  onFocus={() => setFocusedField(field.key)}
                  placeholder={field.placeholder}
                  className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#475569] focus:outline-none focus:border-blue-500"
                />
                {upstreamNodes.length > 0 && field.key !== 'method' && field.key !== 'operator' && (
                  <button
                    onClick={() => setFocusedField(field.key)}
                    className="absolute top-1/2 -translate-y-1/2 right-2 p-1 text-[#475569] hover:text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
                    title="插入变量"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// Node config definitions (mirrors backend)
function getNodeConfigFields(type: string) {
  const configs: Record<string, any[]> = {
    webhook_trigger: [
      { key: 'url_path', label: 'URL 路径', type: 'text', default: '/webhook', placeholder: '/api/webhook', required: true },
      { key: 'method', label: 'HTTP 方法', type: 'select', options: ['GET', 'POST', 'PUT'], default: 'POST' },
    ],
    schedule_trigger: [
      { key: 'cron', label: 'Cron 表达式', type: 'text', default: '0 * * * *', placeholder: '分 时 日 月 周', required: true },
    ],
    http_request: [
      { key: 'url', label: 'URL', type: 'text', default: '', placeholder: 'https://api.example.com/data', required: true },
      { key: 'method', label: '方法', type: 'select', options: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], default: 'GET' },
      { key: 'headers', label: '请求头 (JSON)', type: 'textarea', default: '{}', placeholder: '{"Authorization": "Bearer ..."}' },
      { key: 'body', label: '请求体', type: 'textarea', default: '', placeholder: 'POST/PUT 请求体' },
    ],
    json_parse: [
      { key: 'path', label: 'JSON 路径', type: 'text', default: '', placeholder: 'data.items 或 [0].name' },
    ],
    data_filter: [
      { key: 'field', label: '字段名', type: 'text', default: '', placeholder: 'status', required: true },
      { key: 'operator', label: '操作符', type: 'select', options: ['equals', 'not_equals', 'contains', 'gt', 'lt'], default: 'equals' },
      { key: 'value', label: '值', type: 'text', default: '', placeholder: 'active' },
    ],
    data_transform: [
      { key: 'expression', label: '转换表达式', type: 'textarea', default: '', placeholder: 'data["title"] 或 len(data)', required: true },
    ],
    set_variable: [
      { key: 'name', label: '变量名', type: 'text', default: '', placeholder: 'my_var', required: true },
      { key: 'value', label: '值', type: 'textarea', default: '', placeholder: '字符串、数字或 JSON' },
    ],
    llm_chat: [
      { key: 'api_key', label: 'API Key (可选，留空使用模拟模式)', type: 'text', default: '', placeholder: 'sk-... 不填则返回模拟响应' },
      { key: 'api_base', label: 'API Base URL', type: 'text', default: 'https://api.openai.com/v1', placeholder: 'https://api.openai.com/v1' },
      { key: 'model', label: '模型', type: 'text', default: 'gpt-4o', placeholder: 'gpt-4o' },
      { key: 'system_prompt', label: '系统提示词', type: 'textarea', default: '', placeholder: '你是一个有用的助手' },
      { key: 'user_prompt', label: '用户提示词', type: 'textarea', default: '', placeholder: '点击右侧标签插入上游数据' },
      { key: 'temperature', label: '温度', type: 'number', default: 0.7 },
      { key: 'max_tokens', label: '最大 Token', type: 'number', default: 4096 },
    ],
    text_summarize: [
      { key: 'api_key', label: 'API Key (可选)', type: 'text', default: '', placeholder: '留空使用模拟模式' },
      { key: 'api_base', label: 'API Base URL', type: 'text', default: 'https://api.openai.com/v1' },
      { key: 'model', label: '模型', type: 'text', default: 'gpt-4o' },
      { key: 'max_length', label: '最大长度', type: 'number', default: 200 },
    ],
    text_translate: [
      { key: 'api_key', label: 'API Key (可选)', type: 'text', default: '', placeholder: '留空使用模拟模式' },
      { key: 'api_base', label: 'API Base URL', type: 'text', default: 'https://api.openai.com/v1' },
      { key: 'model', label: '模型', type: 'text', default: 'gpt-4o' },
      { key: 'target_language', label: '目标语言', type: 'select', options: ['中文', 'English', '日本語', '한국어', 'Français', 'Deutsch', 'Español'], default: 'English' },
    ],
    text_classify: [
      { key: 'api_key', label: 'API Key (可选)', type: 'text', default: '', placeholder: '留空使用模拟模式' },
      { key: 'api_base', label: 'API Base URL', type: 'text', default: 'https://api.openai.com/v1' },
      { key: 'model', label: '模型', type: 'text', default: 'gpt-4o' },
      { key: 'categories', label: '分类列表 (逗号分隔)', type: 'text', default: '正面,负面,中性', placeholder: '正面,负面,中性' },
    ],
    agent: [
      { key: 'api_key', label: 'API Key (可选)', type: 'text', default: '', placeholder: '留空使用模拟模式' },
      { key: 'api_base', label: 'API Base URL', type: 'text', default: 'https://api.openai.com/v1' },
      { key: 'model', label: '模型', type: 'text', default: 'gpt-4o' },
      { key: 'system_prompt', label: '系统提示词', type: 'textarea', default: '你是一个有用的AI助手。', placeholder: '定义 Agent 的角色和行为' },
      { key: 'tools', label: '可用工具 (JSON)', type: 'textarea', default: '[]', placeholder: '[{"name":"tool_name","description":"...","parameters":{}}]' },
      { key: 'max_steps', label: '最大推理步数', type: 'number', default: 5 },
    ],
    knowledge_base: [
      { key: 'documents', label: '文档内容 (分隔符分隔)', type: 'textarea', default: '', placeholder: '文档1\n---\n文档2\n---\n文档3', required: true },
      { key: 'top_k', label: '返回条数', type: 'number', default: 3 },
      { key: 'separator', label: '文档分隔符', type: 'text', default: '---' },
    ],
    condition: [
      { key: 'field', label: '字段', type: 'text', default: '', placeholder: 'status', required: true },
      { key: 'operator', label: '操作符', type: 'select', options: ['equals', 'not_equals', 'contains', 'gt', 'lt', 'is_empty', 'is_not_empty'], default: 'equals' },
      { key: 'value', label: '值', type: 'text', default: '', placeholder: 'active' },
    ],
    delay: [
      { key: 'seconds', label: '等待秒数', type: 'number', default: 1 },
    ],
    loop: [
      { key: 'items_path', label: '列表字段路径', type: 'text', default: '', placeholder: 'data.items', required: true },
    ],
    code: [
      { key: 'code', label: 'Python 代码', type: 'textarea', default: 'def main(input_data):\n    return input_data', placeholder: 'def main(input_data):\n    # 处理输入数据\n    return result', required: true },
    ],
    csv_parse: [
      { key: 'delimiter', label: '分隔符', type: 'text', default: ',' },
      { key: 'has_header', label: '包含表头', type: 'select', options: ['true', 'false'], default: 'true' },
    ],
    text_join: [
      { key: 'separator', label: '分隔符', type: 'text', default: ', ', placeholder: ', ' },
      { key: 'field', label: '提取字段 (可选)', type: 'text', default: '', placeholder: 'name' },
    ],
    text_split: [
      { key: 'delimiter', label: '分隔符', type: 'text', default: ',', placeholder: ',' },
      { key: 'trim', label: '去除空白', type: 'select', options: ['true', 'false'], default: 'true' },
    ],
    aggregate: [
      { key: 'operation', label: '操作', type: 'select', options: ['count', 'sum', 'avg', 'min', 'max', 'first', 'last'], default: 'count' },
      { key: 'field', label: '数值字段 (sum/avg 需要)', type: 'text', default: '', placeholder: 'price' },
    ],
    send_email: [
      { key: 'to', label: '收件人', type: 'text', default: '', placeholder: 'user@example.com', required: true },
      { key: 'subject', label: '主题', type: 'text', default: '', placeholder: '邮件主题' },
      { key: 'body', label: '正文', type: 'textarea', default: '', placeholder: '邮件正文内容' },
    ],
    webhook_response: [
      { key: 'url', label: '回调 URL', type: 'text', default: '', placeholder: 'https://example.com/callback', required: true },
      { key: 'method', label: '方法', type: 'select', options: ['POST', 'PUT'], default: 'POST' },
    ],
    save_file: [
      { key: 'filename', label: '文件名', type: 'text', default: 'output.json', placeholder: 'output.json' },
      { key: 'format', label: '格式', type: 'select', options: ['json', 'csv', 'txt'], default: 'json' },
    ],
    log_output: [
      { key: 'message', label: '日志消息', type: 'textarea', default: '', placeholder: '点击右侧标签插入数据引用' },
    ],
  }
  return configs[type] || []
}

function isAiNode(type: string): boolean {
  return ['llm_chat', 'text_summarize', 'text_translate', 'text_classify', 'agent', 'knowledge_base'].includes(type)
}

function getNodeOutputHint(type: string): string | null {
  const hints: Record<string, string> = {
    manual_trigger: '{triggered, time}',
    webhook_trigger: '{triggered, url_path, method}',
    schedule_trigger: '{triggered, cron}',
    http_request: '{status_code, body, headers, success}',
    json_parse: '{value}',
    data_filter: '{filtered, matched, field_value}',
    data_transform: '{transformed}',
    set_variable: '{variable_name: value}',
    csv_parse: '{rows: [...], count}',
    text_join: '{result, count}',
    text_split: '{items: [...], count}',
    aggregate: '{result, input_count, operation}',
    llm_chat: '{response, model}',
    text_summarize: '{summary}',
    text_translate: '{translation, target_language}',
    text_classify: '{category}',
    agent: '{response, steps, tools_used}',
    knowledge_base: '{results: [...], total_docs}',
    condition: '{condition_result, branch: "true"/"false"}',
    delay: '{waited_seconds, input}',
    loop: '{items: [...], count}',
    code: '{output, stdout}',
    log_output: '{logged, message}',
  }
  return hints[type] || null
}
