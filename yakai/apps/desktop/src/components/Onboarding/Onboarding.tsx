import { useState } from 'react'
import { useAppStore } from '../../stores/appStore'
import { useApi } from '../../hooks/useApi'

type Step = 1 | 2 | 3 | 4

interface FormState {
  name: string
  major: string
  apiKey: string
  courseCode: string
  courseName: string
  professor: string
  semester: string
}

const SEMESTER_OPTIONS = ['Fall 2026', 'Spring 2026', 'Summer 2026', 'Fall 2025', 'Spring 2025']

export function Onboarding() {
  const [step, setStep] = useState<Step>(1)
  const [form, setForm] = useState<FormState>({
    name: '', major: '', apiKey: '',
    courseCode: '', courseName: '', professor: '', semester: SEMESTER_OPTIONS[0],
  })
  const [errors, setErrors] = useState<Partial<FormState>>({})
  const [apiKeyValid, setApiKeyValid] = useState<boolean | null>(null)
  const [validatingKey, setValidatingKey] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const setUser = useAppStore((s) => s.setUser)
  const setOnboardingComplete = useAppStore((s) => s.setOnboardingComplete)
  const setSemesters = useAppStore((s) => s.setSemesters)
  const addClass = useAppStore((s) => s.addClass)
  const api = useApi()

  const update = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }))

  function validateStep(): boolean {
    const e: Partial<FormState> = {}
    if (step === 1 && !form.name.trim()) e.name = 'Name is required'
    if (step === 2 && !form.major.trim()) e.major = 'Major is required'
    if (step === 3) {
      if (!form.apiKey.startsWith('sk-')) e.apiKey = 'API key must start with sk-'
      else if (apiKeyValid === false) e.apiKey = 'Key is invalid — check it and try again'
      else if (apiKeyValid === null) e.apiKey = 'Click "Validate Key" before continuing'
    }
    if (step === 4) {
      if (!form.courseCode.trim()) e.courseCode = 'Course code is required'
      if (!form.courseName.trim()) e.courseName = 'Course name is required'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  async function validateKey() {
    if (!form.apiKey.startsWith('sk-')) {
      setErrors({ apiKey: 'API key must start with sk-' })
      return
    }
    setValidatingKey(true)
    setErrors({})
    const valid = await api.validateApiKey(form.apiKey)
    setApiKeyValid(valid)
    setValidatingKey(false)
    if (!valid) setErrors({ apiKey: 'Key is invalid or OpenAI API is unreachable' })
  }

  function next() {
    if (validateStep()) setStep((s) => Math.min(s + 1, 4) as Step)
  }

  function back() {
    setErrors({})
    setStep((s) => Math.max(s - 1, 1) as Step)
  }

  async function finish() {
    if (!validateStep()) return
    setSubmitting(true)
    try {
      const sem = await api.createSemester(form.semester, 'local-user')
      setSemesters([sem])
      const cls = await api.createClass({
        semester_id: sem.id,
        course_code: form.courseCode.toUpperCase(),
        course_name: form.courseName,
        professor: form.professor || undefined,
        major: form.major,
      })
      addClass(cls)
      setUser({ name: form.name, major: form.major, apiKey: form.apiKey })
      setOnboardingComplete(true)
    } catch (err) {
      setErrors({ courseCode: 'Failed to create class. Is the AI engine running?' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 w-full max-w-md shadow-2xl">
        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-6">
          {([1, 2, 3, 4] as Step[]).map((s) => (
            <div
              key={s}
              className={`w-2 h-2 rounded-full transition-colors ${
                s === step ? 'bg-indigo-500' : s < step ? 'bg-indigo-800' : 'bg-gray-700'
              }`}
            />
          ))}
        </div>

        <p className="text-gray-500 text-sm mb-1">Step {step} of 4</p>

        {step === 1 && (
          <div>
            <h1 className="text-gray-100 text-2xl font-bold mb-6">
              Welcome to YakAI — what's your name?
            </h1>
            <input
              type="text"
              placeholder="Your name"
              value={form.name}
              onChange={update('name')}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              autoFocus
            />
            {errors.name && <p className="text-red-400 text-sm mt-2">{errors.name}</p>}
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-gray-100 text-2xl font-bold mb-2">What's your major?</h1>
            <p className="text-gray-500 text-sm mb-6">
              YakAI uses this to give better suggestions when you archive courses or set up class inheritance.
            </p>
            <input
              type="text"
              placeholder="e.g. Electrical Engineering"
              value={form.major}
              onChange={update('major')}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              autoFocus
            />
            {errors.major && <p className="text-red-400 text-sm mt-2">{errors.major}</p>}
          </div>
        )}

        {step === 3 && (
          <div>
            <h1 className="text-gray-100 text-2xl font-bold mb-2">Add your OpenAI API key</h1>
            <p className="text-gray-400 text-sm mb-4">YakAI uses OpenAI to power your class AI. You'll need your own API key.</p>
            <ol className="text-gray-500 text-xs mb-5 space-y-1 list-decimal list-inside">
              <li>Go to platform.openai.com</li>
              <li>Sign in or create a free account</li>
              <li>Click your profile → "API Keys"</li>
              <li>Click "Create new secret key"</li>
              <li>Copy the key and paste it below</li>
            </ol>
            <div className="flex gap-2">
              <input
                type="password"
                placeholder="sk-..."
                value={form.apiKey}
                onChange={(e) => { update('apiKey')(e); setApiKeyValid(null) }}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono"
                autoFocus
              />
              <button
                type="button"
                onClick={validateKey}
                disabled={validatingKey}
                className="px-4 py-3 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-gray-200 text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
              >
                {validatingKey ? 'Checking...' : 'Validate Key'}
              </button>
            </div>
            {errors.apiKey && <p className="text-red-400 text-sm mt-2">{errors.apiKey}</p>}
            {apiKeyValid === true && (
              <p className="text-green-400 text-sm mt-2">Key verified — you're good to go!</p>
            )}
            <p className="text-gray-600 text-xs mt-4">
              Typical cost: $5–25/semester depending on how much material you add.
            </p>
          </div>
        )}

        {step === 4 && (
          <div>
            <h1 className="text-gray-100 text-2xl font-bold mb-6">Create your first class</h1>
            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm mb-1 block">Course code</label>
                <input
                  type="text"
                  placeholder="ENGR2410"
                  value={form.courseCode}
                  onChange={update('courseCode')}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
                {errors.courseCode && <p className="text-red-400 text-sm mt-1">{errors.courseCode}</p>}
              </div>
              <div>
                <label className="text-gray-400 text-sm mb-1 block">Course name</label>
                <input
                  type="text"
                  placeholder="Circuit Analysis"
                  value={form.courseName}
                  onChange={update('courseName')}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
                {errors.courseName && <p className="text-red-400 text-sm mt-1">{errors.courseName}</p>}
              </div>
              <div>
                <label className="text-gray-400 text-sm mb-1 block">Professor</label>
                <input
                  type="text"
                  placeholder="Dr. Smith"
                  value={form.professor}
                  onChange={update('professor')}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm mb-1 block">Semester</label>
                <select
                  value={form.semester}
                  onChange={update('semester')}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-gray-100 focus:outline-none focus:border-indigo-500"
                >
                  {SEMESTER_OPTIONS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-8">
          {step > 1 && (
            <button
              onClick={back}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium py-2.5 px-4 rounded-lg transition-colors"
            >
              Back
            </button>
          )}
          {step < 4 ? (
            <button
              onClick={next}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              onClick={finish}
              disabled={submitting}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
            >
              {submitting ? 'Setting up...' : 'Start YakAI'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
