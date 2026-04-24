import { useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { Lecture, QuizAttemptResult, QuizQuestion } from '../../types'
import { QuizResults } from './QuizResults'

interface Props {
  classId: string
  lectures: Lecture[]
}

type Scope = 'full' | 'lecture' | 'weak-areas'
type Phase = 'setup' | 'active' | 'results'

const SCOPE_LABELS: Record<Scope, string> = {
  full: 'All Material',
  lecture: 'Single Lecture',
  'weak-areas': 'Weak Areas',
}

const NUM_OPTIONS = [5, 10, 20]

export function QuizScreen({ classId, lectures }: Props) {
  const [phase, setPhase] = useState<Phase>('setup')
  const [scope, setScope] = useState<Scope>('full')
  const [numQuestions, setNumQuestions] = useState(10)
  const [selectedLectureId, setSelectedLectureId] = useState<string>('')
  const [generating, setGenerating] = useState(false)
  const [genError, setGenError] = useState<string | null>(null)

  const [sessionId, setSessionId] = useState('')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [hintsShown, setHintsShown] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [currentResult, setCurrentResult] = useState<QuizAttemptResult | null>(null)
  const [results, setResults] = useState<Record<string, QuizAttemptResult>>({})
  const [startTime, setStartTime] = useState(0)

  const api = useApi()

  async function handleStart() {
    setGenerating(true)
    setGenError(null)
    try {
      const data = await api.generateQuiz(
        classId,
        scope,
        numQuestions,
        scope === 'lecture' && selectedLectureId ? selectedLectureId : undefined
      )
      setSessionId(data.session_id)
      setQuestions(data.questions)
      setCurrentIdx(0)
      setResults({})
      setUserAnswer('')
      setHintsShown(0)
      setSubmitted(false)
      setCurrentResult(null)
      setStartTime(Date.now())
      setPhase('active')
    } catch {
      setGenError('Failed to generate quiz. Make sure you have uploaded class materials.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleSubmit() {
    const q = questions[currentIdx]
    if (!q || !userAnswer.trim() || submitting) return
    setSubmitting(true)
    const timeTaken = Math.round((Date.now() - startTime) / 1000)
    try {
      const result = await api.submitQuizAttempt(
        sessionId, q.id, userAnswer, hintsShown, timeTaken
      )
      setCurrentResult(result)
      setResults((prev) => ({ ...prev, [q.id]: result }))
      setSubmitted(true)
    } catch {
      setSubmitted(true)
      const fallback: QuizAttemptResult = { is_correct: false, correct_answer: '', explanation: '' }
      setCurrentResult(fallback)
      setResults((prev) => ({ ...prev, [q.id]: fallback }))
    } finally {
      setSubmitting(false)
    }
  }

  function handleNext() {
    if (currentIdx + 1 >= questions.length) {
      setPhase('results')
      return
    }
    setCurrentIdx((i) => i + 1)
    setUserAnswer('')
    setHintsShown(0)
    setSubmitted(false)
    setCurrentResult(null)
    setStartTime(Date.now())
  }

  function handleRetry() {
    setPhase('setup')
    setQuestions([])
    setResults({})
  }

  const q = questions[currentIdx]
  const hints = q ? [q.hint_level_1, q.hint_level_2, q.hint_level_3].filter(Boolean) as string[] : []

  if (phase === 'results') {
    return (
      <QuizResults
        sessionId={sessionId}
        questions={questions}
        results={results}
        onRetry={handleRetry}
        onDone={handleRetry}
      />
    )
  }

  if (phase === 'setup') {
    return (
      <div className="flex flex-col gap-6 p-6 max-w-lg mx-auto">
        <h2 className="text-gray-100 text-lg font-semibold">Configure Quiz</h2>

        {/* Scope */}
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Scope</p>
          <div className="flex gap-2 flex-wrap">
            {(Object.keys(SCOPE_LABELS) as Scope[]).map((s) => (
              <button
                key={s}
                onClick={() => setScope(s)}
                className={`text-sm px-4 py-2 rounded-lg border transition-colors ${
                  scope === s
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-gray-900 border-gray-700 text-gray-400 hover:border-gray-600'
                }`}
              >
                {SCOPE_LABELS[s]}
              </button>
            ))}
          </div>
        </div>

        {/* Lecture picker */}
        {scope === 'lecture' && lectures.length > 0 && (
          <div>
            <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Lecture</p>
            <select
              value={selectedLectureId}
              onChange={(e) => setSelectedLectureId(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 text-gray-100 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select a lecture...</option>
              {lectures.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.number ? `Lecture ${l.number}` : ''}{l.title ? ` — ${l.title}` : ''}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Num questions */}
        <div>
          <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Questions</p>
          <div className="flex gap-2">
            {NUM_OPTIONS.map((n) => (
              <button
                key={n}
                onClick={() => setNumQuestions(n)}
                className={`text-sm px-4 py-2 rounded-lg border transition-colors ${
                  numQuestions === n
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-gray-900 border-gray-700 text-gray-400 hover:border-gray-600'
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        {genError && <p className="text-red-400 text-sm">{genError}</p>}

        <button
          onClick={handleStart}
          disabled={generating || (scope === 'lecture' && !selectedLectureId)}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm py-3 rounded-xl transition-colors font-medium"
        >
          {generating ? 'Generating...' : 'Start Quiz'}
        </button>
      </div>
    )
  }

  if (!q) return null

  const isMcq = q.question_type === 'mcq'
  const mcqOptions = q.options ?? []

  return (
    <div className="flex flex-col gap-5 p-6 max-w-2xl mx-auto">
      {/* Progress */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Question {currentIdx + 1} of {questions.length}</span>
          {q.topic_tag && <span className="text-indigo-400">{q.topic_tag}</span>}
        </div>
        <div className="bg-gray-800 rounded-full h-1.5">
          <div
            className="bg-indigo-500 h-1.5 rounded-full transition-all"
            style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <p className="text-gray-100 text-base leading-relaxed">{q.question_text}</p>
      </div>

      {/* Answer input */}
      {isMcq && mcqOptions.length > 0 ? (
        <div className="space-y-2">
          {mcqOptions.map((opt) => (
            <label
              key={opt}
              className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                userAnswer === opt
                  ? 'border-indigo-500 bg-indigo-950'
                  : 'border-gray-800 bg-gray-900 hover:border-gray-700'
              }`}
            >
              <input
                type="radio"
                name="mcq"
                value={opt}
                checked={userAnswer === opt}
                onChange={() => !submitted && setUserAnswer(opt)}
                disabled={submitted}
                className="accent-indigo-500"
              />
              <span className="text-gray-200 text-sm">{opt}</span>
            </label>
          ))}
        </div>
      ) : (
        <textarea
          value={userAnswer}
          onChange={(e) => !submitted && setUserAnswer(e.target.value)}
          disabled={submitted}
          placeholder="Type your answer..."
          rows={4}
          className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 text-sm placeholder-gray-600 resize-none focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-60"
        />
      )}

      {/* Hints */}
      {hints.length > 0 && !submitted && (
        <div className="space-y-2">
          {hints.slice(0, hintsShown).map((h, i) => (
            <div key={i} className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-gray-400 text-sm">
              <span className="text-yellow-400 text-xs font-medium mr-2">Hint {i + 1}</span>{h}
            </div>
          ))}
          {hintsShown < hints.length && (
            <button
              onClick={() => setHintsShown((n) => n + 1)}
              className="text-yellow-400 text-xs hover:text-yellow-300 transition-colors"
            >
              Show hint {hintsShown + 1} of {hints.length}
            </button>
          )}
        </div>
      )}

      {/* Result feedback */}
      {submitted && currentResult && (
        <div
          className={`rounded-xl p-4 border ${
            currentResult.is_correct
              ? 'bg-green-950 border-green-800 text-green-300'
              : 'bg-red-950 border-red-800 text-red-300'
          }`}
        >
          <p className="font-semibold text-sm mb-1">
            {currentResult.is_correct ? '✓ Correct!' : '✗ Incorrect'}
          </p>
          {!currentResult.is_correct && currentResult.correct_answer && (
            <p className="text-xs mb-1">
              Correct answer: <span className="text-gray-200">{currentResult.correct_answer}</span>
            </p>
          )}
          {currentResult.explanation && (
            <p className="text-xs opacity-80">{currentResult.explanation}</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        {!submitted ? (
          <button
            onClick={handleSubmit}
            disabled={!userAnswer.trim() || submitting}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm py-2.5 rounded-xl transition-colors"
          >
            {submitting ? 'Checking...' : 'Submit Answer'}
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-sm py-2.5 rounded-xl transition-colors"
          >
            {currentIdx + 1 >= questions.length ? 'See Results' : 'Next Question'}
          </button>
        )}
      </div>
    </div>
  )
}
