import type { QuizAttemptResult, QuizQuestion } from '../../types'

interface Props {
  sessionId: string
  questions: QuizQuestion[]
  results: Record<string, QuizAttemptResult>
  onRetry: () => void
  onDone: () => void
}

export function QuizResults({ questions, results, onRetry, onDone }: Props) {
  const answered = questions.filter((q) => results[q.id])
  const correct = answered.filter((q) => results[q.id]?.is_correct).length
  const total = questions.length
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0

  const topicMap: Record<string, { correct: number; total: number }> = {}
  for (const q of questions) {
    const tag = q.topic_tag ?? 'General'
    if (!topicMap[tag]) topicMap[tag] = { correct: 0, total: 0 }
    topicMap[tag].total++
    if (results[q.id]?.is_correct) topicMap[tag].correct++
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-2xl mx-auto">
      {/* Score */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
        <p className="text-gray-400 text-sm mb-1">Final Score</p>
        <p className="text-4xl font-bold text-gray-100">{correct} / {total}</p>
        <p
          className={`text-lg font-semibold mt-1 ${
            pct >= 70 ? 'text-green-400' : pct >= 40 ? 'text-yellow-400' : 'text-red-400'
          }`}
        >
          {pct}%
        </p>
      </div>

      {/* Topic breakdown */}
      {Object.keys(topicMap).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">
            Topic Breakdown
          </h3>
          <div className="space-y-2">
            {Object.entries(topicMap).map(([tag, { correct: c, total: t }]) => {
              const acc = Math.round((c / t) * 100)
              const color = acc >= 70 ? 'bg-green-500' : acc >= 40 ? 'bg-yellow-500' : 'bg-red-500'
              return (
                <div key={tag} className="flex items-center gap-3">
                  <span className="text-gray-300 text-sm w-32 truncate">{tag}</span>
                  <div className="flex-1 bg-gray-800 rounded-full h-2">
                    <div className={`${color} h-2 rounded-full`} style={{ width: `${acc}%` }} />
                  </div>
                  <span className="text-gray-400 text-xs w-10 text-right">{c}/{t}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Question review */}
      <div className="space-y-3">
        <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider">
          Question Review
        </h3>
        {questions.map((q, i) => {
          const result = results[q.id]
          if (!result) return null
          return (
            <div
              key={q.id}
              className={`bg-gray-900 border rounded-xl p-4 ${
                result.is_correct ? 'border-green-800' : 'border-red-800'
              }`}
            >
              <div className="flex items-start gap-2">
                <span className={`text-sm font-medium ${result.is_correct ? 'text-green-400' : 'text-red-400'}`}>
                  {result.is_correct ? '✓' : '✗'}
                </span>
                <div className="flex-1">
                  <p className="text-gray-200 text-sm">{i + 1}. {q.question_text}</p>
                  {!result.is_correct && (
                    <p className="text-gray-500 text-xs mt-1">
                      Correct: <span className="text-gray-300">{result.correct_answer}</span>
                    </p>
                  )}
                  {result.explanation && (
                    <p className="text-gray-500 text-xs mt-1 italic">{result.explanation}</p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onRetry}
          className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-sm py-2.5 rounded-xl transition-colors"
        >
          Try Again
        </button>
        <button
          onClick={onDone}
          className="flex-1 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm py-2.5 rounded-xl transition-colors"
        >
          Back to Hub
        </button>
      </div>
    </div>
  )
}
