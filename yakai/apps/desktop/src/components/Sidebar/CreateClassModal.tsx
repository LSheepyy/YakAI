import { useState } from 'react'
import { useApi } from '../../hooks/useApi'
import { useAppStore } from '../../stores/appStore'

interface Props {
  onClose: () => void
}

export function CreateClassModal({ onClose }: Props) {
  const [courseCode, setCourseCode] = useState('')
  const [courseName, setCourseName] = useState('')
  const [professor, setProfessor] = useState('')
  const [semesterInput, setSemesterInput] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const semesters = useAppStore((s) => s.semesters)
  const setSemesters = useAppStore((s) => s.setSemesters)
  const addClass = useAppStore((s) => s.addClass)
  const api = useApi()

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!courseCode.trim()) { setError('Course code is required'); return }
    if (!courseName.trim()) { setError('Course name is required'); return }
    if (!semesterInput.trim()) { setError('Semester is required'); return }

    setSubmitting(true)
    setError('')
    try {
      // Find or create semester
      let sem = semesters.find((s) => s.name === semesterInput.trim())
      if (!sem) {
        sem = await api.createSemester(semesterInput.trim(), 'local-user')
        setSemesters([...semesters, sem])
      }
      const cls = await api.createClass({
        semester_id: sem.id,
        course_code: courseCode.toUpperCase().trim(),
        course_name: courseName.trim(),
        professor: professor.trim() || undefined,
      })
      addClass(cls)
      onClose()
    } catch {
      setError('Failed to create class. Is the AI engine running?')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
        <h2 className="text-gray-100 text-lg font-bold mb-5">New Class</h2>
        <form onSubmit={submit} className="space-y-3">
          <input
            type="text"
            placeholder="Course code (e.g. ENGR2410)"
            value={courseCode}
            onChange={(e) => setCourseCode(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            placeholder="Course name"
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            placeholder="Professor"
            value={professor}
            onChange={(e) => setProfessor(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-500"
          />
          <input
            type="text"
            placeholder="Semester (e.g. Fall 2026)"
            value={semesterInput}
            onChange={(e) => setSemesterInput(e.target.value)}
            list="semesters-list"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-gray-100 placeholder-gray-500 text-sm focus:outline-none focus:border-indigo-500"
          />
          <datalist id="semesters-list">
            {semesters.map((s) => <option key={s.id} value={s.name} />)}
          </datalist>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm py-2 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm py-2 rounded-lg transition-colors"
            >
              {submitting ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
