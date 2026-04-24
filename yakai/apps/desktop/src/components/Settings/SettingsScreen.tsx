import { useEffect, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { CostSummary } from '../../types'

interface Props {
  onClose: () => void
}

type KeyStatus = 'idle' | 'saving' | 'valid' | 'invalid'

export function SettingsScreen({ onClose }: Props) {
  const [apiKey, setApiKey] = useState('')
  const [keyStatus, setKeyStatus] = useState<KeyStatus>('idle')

  const [costSummary, setCostSummary] = useState<CostSummary | null>(null)
  const [costLoading, setCostLoading] = useState(false)

  const api = useApi()

  useEffect(() => {
    loadCost()
  }, [])

  async function loadCost() {
    setCostLoading(true)
    try {
      const data = await api.getCostSummary()
      setCostSummary(data)
    } catch {
      setCostSummary(null)
    } finally {
      setCostLoading(false)
    }
  }

  async function handleSaveKey() {
    if (!apiKey.trim() || keyStatus === 'saving') return
    setKeyStatus('saving')
    try {
      const res = await api.setApiKey(apiKey.trim())
      setKeyStatus(res.valid ? 'valid' : 'invalid')
    } catch {
      setKeyStatus('invalid')
    }
  }

  function formatCost(val: number) {
    return val < 0.01 ? '<$0.01' : `$${val.toFixed(2)}`
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <h2 className="text-gray-100 text-lg font-semibold">Settings</h2>
        <button
          onClick={onClose}
          className="text-gray-600 hover:text-gray-400 text-xl leading-none transition-colors"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8 max-w-2xl">
        {/* API Key section */}
        <section>
          <h3 className="text-gray-300 font-medium mb-4">OpenAI API Key</h3>
          <div className="flex gap-3">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => { setApiKey(e.target.value); setKeyStatus('idle') }}
              placeholder="sk-..."
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-100 text-sm placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <button
              onClick={handleSaveKey}
              disabled={!apiKey.trim() || keyStatus === 'saving'}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm px-4 py-2.5 rounded-xl transition-colors whitespace-nowrap"
            >
              {keyStatus === 'saving' ? 'Verifying...' : 'Save & Verify'}
            </button>
          </div>
          {keyStatus === 'valid' && (
            <p className="text-green-400 text-sm mt-2">✓ Connected</p>
          )}
          {keyStatus === 'invalid' && (
            <p className="text-red-400 text-sm mt-2">✗ Invalid key</p>
          )}
        </section>

        {/* Cost Summary section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-gray-300 font-medium">API Cost Summary</h3>
            <button
              onClick={loadCost}
              className="text-indigo-400 hover:text-indigo-300 text-xs transition-colors"
            >
              Refresh
            </button>
          </div>

          {costLoading && (
            <div className="flex justify-center py-6">
              <div className="w-4 h-4 rounded-full bg-indigo-500 animate-pulse" />
            </div>
          )}

          {!costLoading && costSummary && (
            <div className="space-y-4">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">Total spend</p>
                <p className="text-2xl font-bold text-gray-100">{formatCost(costSummary.total_cost)}</p>
              </div>

              {Object.keys(costSummary.by_feature).length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                  <p className="text-gray-500 text-xs uppercase tracking-wider px-4 pt-3 pb-2">By Feature</p>
                  {Object.entries(costSummary.by_feature).map(([feat, cost]) => (
                    <div key={feat} className="flex justify-between items-center px-4 py-2 border-t border-gray-800">
                      <span className="text-gray-300 text-sm capitalize">{feat}</span>
                      <span className="text-gray-400 text-sm">{formatCost(cost)}</span>
                    </div>
                  ))}
                </div>
              )}

              {Object.keys(costSummary.by_model).length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                  <p className="text-gray-500 text-xs uppercase tracking-wider px-4 pt-3 pb-2">By Model</p>
                  {Object.entries(costSummary.by_model).map(([model, cost]) => (
                    <div key={model} className="flex justify-between items-center px-4 py-2 border-t border-gray-800">
                      <span className="text-gray-300 text-sm">{model}</span>
                      <span className="text-gray-400 text-sm">{formatCost(cost)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {!costLoading && !costSummary && (
            <p className="text-gray-600 text-sm">Could not load cost data.</p>
          )}
        </section>
      </div>
    </div>
  )
}
