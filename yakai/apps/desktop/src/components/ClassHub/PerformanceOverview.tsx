import { useEffect, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { TopicPerformance } from '../../types'

interface Props {
  classId: string
}

export function PerformanceOverview({ classId }: Props) {
  const [topics, setTopics] = useState<TopicPerformance[]>([])
  const [loading, setLoading] = useState(true)
  const api = useApi()

  useEffect(() => {
    setLoading(true)
    api.getPerformance(classId)
      .then(setTopics)
      .catch(() => setTopics([]))
      .finally(() => setLoading(false))
  }, [classId])

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Performance</h3>

      {loading && (
        <div className="flex justify-center py-4">
          <div className="w-4 h-4 rounded-full bg-indigo-500 animate-pulse" />
        </div>
      )}

      {!loading && topics.length === 0 && (
        <p className="text-gray-600 text-sm">No quiz data yet. Take a quiz to see your performance.</p>
      )}

      {!loading && topics.length > 0 && (
        <div className="space-y-3">
          {topics.map((t) => {
            const pct = Math.round(t.accuracy_rate * 100)
            const barColor = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500'
            const labelColor = pct >= 70 ? 'text-green-400' : pct >= 40 ? 'text-yellow-400' : 'text-red-400'
            return (
              <div key={t.id} className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 w-36 shrink-0">
                  {pct < 40 && <span className="text-yellow-400 text-xs">⚠</span>}
                  <span className="text-gray-300 text-sm truncate">{t.topic_tag}</span>
                </div>
                <div className="flex-1 bg-gray-800 rounded-full h-2">
                  <div
                    className={`${barColor} h-2 rounded-full transition-all`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className={`${labelColor} text-xs w-10 text-right`}>{pct}%</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
