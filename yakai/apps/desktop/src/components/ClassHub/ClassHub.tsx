import { useEffect, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { ClassDetail } from '../../types'
import { FileDropZone } from './FileDropZone'
import { GradingCard } from './GradingCard'
import { ProfessorCard } from './ProfessorCard'
import { ScheduleList } from './ScheduleList'

interface Props {
  classId: string
}

const ACTION_BUTTONS = [
  { label: '💬 Chat', key: 'chat' },
  { label: '📝 Quiz Me', key: 'quiz' },
  { label: '🧪 Practice Exam', key: 'exam' },
  { label: '🏠 Homework Help', key: 'hw' },
  { label: '📋 Summary', key: 'summary' },
  { label: '🎙 Record Lecture', key: 'record' },
]

export function ClassHub({ classId }: Props) {
  const [cls, setCls] = useState<ClassDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const api = useApi()

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.getClass(classId)
      .then(setCls)
      .catch(() => setError('Failed to load class'))
      .finally(() => setLoading(false))
  }, [classId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-5 h-5 rounded-full bg-indigo-500 animate-pulse" />
      </div>
    )
  }

  if (error || !cls) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-400">{error ?? 'Class not found'}</p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-gray-100 text-2xl font-bold">
          {cls.course_code} — {cls.course_name}
        </h1>
        {cls.professor && (
          <p className="text-gray-500 text-sm mt-0.5">{cls.professor}</p>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        <FileDropZone classId={classId} />
      </div>
      <div className="flex flex-wrap gap-2">
        {ACTION_BUTTONS.map((btn) => (
          <button
            key={btn.key}
            className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Syllabus banner or professor/grading */}
      {!cls.professor_info ? (
        <div className="bg-gray-900 border border-yellow-800 rounded-xl p-4 flex items-center justify-between">
          <p className="text-yellow-300 text-sm">
            No syllabus added yet. Add it to pre-fill your schedule, calendar, and professor info.
          </p>
          <button className="text-sm bg-yellow-700 hover:bg-yellow-600 text-white px-4 py-1.5 rounded-lg transition-colors whitespace-nowrap ml-4">
            + Add Syllabus
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ProfessorCard professor={cls.professor_info} tas={cls.ta_info} />
          {cls.grading_weights.length > 0 && (
            <GradingCard weights={cls.grading_weights} />
          )}
        </div>
      )}

      {/* Performance overview placeholder */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Performance</h3>
        <p className="text-gray-600 text-sm">No quiz data yet. Take a quiz to see your performance.</p>
      </div>

      {/* Schedule */}
      <ScheduleList lectures={cls.lectures} />
    </div>
  )
}
