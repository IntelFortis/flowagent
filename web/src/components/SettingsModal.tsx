import { useState, useEffect } from 'react'

interface Settings {
  api_key: string
  api_base: string
  default_model: string
}

const STORAGE_KEY = 'flowagent_settings'

function loadSettings(): Settings {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return JSON.parse(saved)
  } catch {}
  return { api_key: '', api_base: 'https://api.openai.com/v1', default_model: 'gpt-4o' }
}

export function getSettings(): Settings {
  return loadSettings()
}

export default function SettingsModal({ onClose }: { onClose: () => void }) {
  const [settings, setSettings] = useState<Settings>(loadSettings())
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl w-[480px] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="p-4 border-b border-[#334155] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm">模型设置</h3>
              <p className="text-xs text-[#64748b]">配置 AI 节点的全局默认参数</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-[#334155] rounded transition-colors">
            <svg className="w-4 h-4 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#94a3b8] mb-1.5">
              API Key
            </label>
            <input
              type="password"
              value={settings.api_key}
              onChange={e => setSettings({ ...settings, api_key: e.target.value })}
              placeholder="sk-..."
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#475569] focus:outline-none focus:border-blue-500"
            />
            <p className="text-[10px] text-[#475569] mt-1">所有 AI 节点将使用此 Key（节点单独配置优先）</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-[#94a3b8] mb-1.5">
              API Base URL
            </label>
            <input
              type="text"
              value={settings.api_base}
              onChange={e => setSettings({ ...settings, api_base: e.target.value })}
              placeholder="https://api.openai.com/v1"
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#475569] focus:outline-none focus:border-blue-500"
            />
            <p className="text-[10px] text-[#475569] mt-1">支持 OpenAI 兼容接口（如 DeepSeek、Moonshot 等）</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-[#94a3b8] mb-1.5">
              默认模型
            </label>
            <div className="grid grid-cols-2 gap-2">
              {['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'deepseek-chat'].map(model => (
                <button
                  key={model}
                  onClick={() => setSettings({ ...settings, default_model: model })}
                  className={`px-3 py-2 rounded-lg text-xs font-mono border transition-colors ${
                    settings.default_model === model
                      ? 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                      : 'bg-[#0f172a] border-[#334155] text-[#94a3b8] hover:border-[#475569]'
                  }`}
                >
                  {model}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-[#0f172a] rounded-lg p-3 border border-[#334155]">
            <p className="text-xs text-[#64748b]">
              <span className="text-[#94a3b8] font-medium">提示：</span>
              不配置 API Key 时，AI 节点将以模拟模式运行，返回示例数据。配置后即可调用真实 AI 接口。
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#334155] flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-[#94a3b8] hover:text-white transition-colors">
            取消
          </button>
          <button
            onClick={handleSave}
            className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${
              saved
                ? 'bg-green-600 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {saved ? '已保存' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  )
}
