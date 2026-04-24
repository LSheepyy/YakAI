import { useState } from 'react'
import { useApi } from '../../hooks/useApi'

interface Props {
  classId: string
}

interface HWResult {
  answer: string
  sources: string[]
  sufficient_knowledge: boolean
}

function renderContent(text: string) {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let inCode = false
  let codeBuffer: string[] = []
  let key = 0

  for (const line of lines) {
    if (line.startsWith('```')) {
      if (inCode) {
        elements.push(
          <pre key={key++} className="bg-gray-800 rounded p-2 my-1 text-xs overflow-x-auto text-gray-200">
            {codeBuffer.join('\n')}
          </pre>
        )
        codeBuffer = []
        inCode = false
      } else {
        inCode = true
      }
      continue
    }
    if (inCode) { codeBuffer.push(line); continue }
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    elements.push(
      <span key={key++}>
        {parts.map((p, i) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={i} className="font-semibold text-gray-100">{p.slice(2, -2)}</strong>
            : p
        )}
        <br />
      </span>
    )
  }
  return elements
}

export function HomeworkScreen({ classId }: Props) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<HWResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const api = useApi()

  async function handleSubmit() {
    if (!question.trim() || loading) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.askHomework(classId, question)
      setResult(res)
    } catch {
      setError('Failed to get an answer. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-5 p-6 max-w-2xl mx-auto">
      <h2 className="text-gray-100 text-lg font-semibold">Homework Help</h2>

      {/* Question input */}
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Paste your homework question here..."
        rows={5}
        className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 text-sm placeholder-gray-600 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
      />

      <button
        onClick={handleSubmit}
        disabled={!question.trim() || loading}
        className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm py-3 rounded-xl transition-colors font-medium"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Getting help...
          </span>
        ) : 'Get Help'}
      </button>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {result && (
        <div className="space-y-4">
          {/* Insufficient knowledge banner */}
          {!result.sufficient_knowledge && (
            <div className="bg-yellow-950 border border-yellow-700 rounded-xl p-4 flex items-start gap-3">
              <span className="text-yellow-400 text-base">⚠</span>
              <p className="text-yellow-300 text-sm">
                I don't have enough training on this topic yet. Try adding your textbook or lecture notes.
              </p>
            </div>
          )}

          {/* Answer */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Answer</h3>
            <div className="text-gray-200 text-sm leading-relaxed">
              {renderContent(result.answer)}
            </div>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div>
              <p className="text-gray-500 text-xs mb-2">Sources used</p>
              <div className="flex flex-wrap gap-2">
                {result.sources.map((src) => (
                  <span
                    key={src}
                    className="bg-indigo-950 border border-indigo-800 text-indigo-300 text-xs px-3 py-1 rounded-full"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
