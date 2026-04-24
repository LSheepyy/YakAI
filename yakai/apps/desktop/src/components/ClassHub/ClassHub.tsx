import { useEffect, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { ClassDetail } from '../../types'
import { ChatScreen } from '../Chat/ChatScreen'
import { HomeworkScreen } from '../Homework/HomeworkScreen'
import { QuizScreen } from '../Quiz/QuizScreen'
import { SearchModal } from '../Search/SearchModal'
import { FileDropZone } from './FileDropZone'
import { GradingCard } from './GradingCard'
import { PerformanceOverview } from './PerformanceOverview'
import { ProfessorCard } from './ProfessorCard'
import { ScheduleList } from './ScheduleList'

interface Props {
  classId: string
}

type SubScreen = 'hub' | 'chat' | 'quiz' | 'homework'

export function ClassHub({ classId }: Props) {
  const [cls, setCls] = useState<ClassDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [subScreen, setSubScreen] = useState<SubScreen>('hub')
  const [showSearch, setShowSearch] = useState(false)
  const api = useApi()

  useEffect(() => {
    setLoading(true)
    setError(null)
    setSubScreen('hub')
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

  const classHeader = (
    <div className="px-6 pt-6 pb-4 border-b border-gray-800">
      <div className="flex items-start justify-between">
        <div>
          {subScreen !== 'hub' && (
            <button
              onClick={() => setSubScreen('hub')}
              className="text-indigo-400 hover:text-indigo-300 text-xs mb-2 flex items-center gap-1 transition-colors"
            >
              ← Back to Hub
            </button>
          )}
          <h1 className="text-gray-100 text-xl font-bold">
            {cls.course_code} — {cls.course_name}
          </h1>
          {cls.professor && (
            <p className="text-gray-500 text-sm mt-0.5">{cls.professor}</p>
          )}
        </div>
        {subScreen === 'hub' && (
          <button
            onClick={() => setShowSearch(true)}
            className="text-gray-500 hover:text-gray-300 text-xl leading-none transition-colors mt-1"
            title="Search class materials"
          >
            🔍
          </button>
        )}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-full">
      {classHeader}

      <div className="flex-1 overflow-y-auto">
        {subScreen === 'chat' && <ChatScreen classId={classId} />}
        {subScreen === 'quiz' && <QuizScreen classId={classId} lectures={cls.lectures} />}
        {subScreen === 'homework' && <HomeworkScreen classId={classId} />}

        {subScreen === 'hub' && (
          <div className="p-6 space-y-6 max-w-4xl mx-auto">
            {/* Action buttons */}
            <div className="flex flex-wrap gap-2">
              <FileDropZone classId={classId} />
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSubScreen('chat')}
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                💬 Chat
              </button>
              <button
                onClick={() => setSubScreen('quiz')}
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                📝 Quiz Me
              </button>
              <button
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                🧪 Practice Exam
              </button>
              <button
                onClick={() => setSubScreen('homework')}
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                🏠 Homework Help
              </button>
              <button
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                📋 Summary
              </button>
              <button
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                🎙 Record Lecture
              </button>
              <button
                onClick={() => setShowSearch(true)}
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm px-4 py-2 rounded-lg transition-colors"
              >
                🔍 Search
              </button>
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

            {/* Performance overview */}
            <PerformanceOverview classId={classId} />

            {/* Schedule */}
            <ScheduleList lectures={cls.lectures} />
          </div>
        )}
      </div>

      {showSearch && (
        <SearchModal classId={classId} onClose={() => setShowSearch(false)} />
      )}
    </div>
  )
}
