import type { Lecture } from '../../types'

interface Props {
  lectures: Lecture[]
}

export function ScheduleList({ lectures }: Props) {
  if (lectures.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Schedule</h3>
        <p className="text-gray-600 text-sm">No lectures yet. Add a syllabus to pre-fill the schedule.</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Schedule</h3>
      <div className="space-y-2">
        {lectures.map((lec) => {
          const hasRecording = Boolean(lec.reference_file_path)
          return (
            <div key={lec.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
              <div className="flex items-center gap-3">
                <span className="text-base" aria-hidden="true">{hasRecording ? '✅' : '○'}</span>
                <div>
                  <span className="text-gray-300 text-sm font-medium">
                    {lec.date ? `${lec.date} — ` : ''}{lec.title ?? 'Untitled'}
                  </span>
                </div>
              </div>
              <button className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors whitespace-nowrap ml-4">
                {hasRecording ? '🎙 recorded' : '+ Attach recording'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
