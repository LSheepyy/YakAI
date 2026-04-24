import { useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { SyllabusData } from '../../types'

interface Props {
  classId: string
  fileId: string
  data: SyllabusData
  onSaved: () => void
  onSkip: () => void
}

export function SyllabusConfirmModal({ classId, fileId, data, onSaved, onSkip }: Props) {
  const [saving, setSaving] = useState(false)
  const api = useApi()

  async function handleSave() {
    setSaving(true)
    try {
      await api.confirmSyllabus(classId, fileId, data as Record<string, unknown>)
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  const professor = data.professor
  const tas = data.tas ?? []
  const grading = data.grading ?? []
  const events = data.events ?? []
  const schedule = data.schedule ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-800">
          <h2 className="text-gray-100 font-bold text-xl">Review extracted syllabus</h2>
          <p className="text-gray-500 text-sm mt-1">
            YakAI extracted the data below. Review it, then save.
          </p>
        </div>

        {/* Scrollable content */}
        <div className="overflow-y-auto flex-1 px-6 py-4 space-y-5">
          {/* Professor */}
          {professor && (
            <Section title="Professor">
              <Row label="Name" value={professor.name} />
              <Row label="Email" value={professor.email} />
              <Row label="Office" value={professor.office} />
              <Row label="Office hours" value={professor.office_hours} />
            </Section>
          )}

          {/* TAs */}
          {tas.length > 0 && (
            <Section title="Teaching Assistants">
              {tas.map((ta, i) => (
                <div key={i} className="text-sm text-gray-300">
                  {ta.name}
                  {ta.email && <span className="text-gray-500 ml-2">{ta.email}</span>}
                  {ta.office_hours && (
                    <span className="text-gray-600 ml-2 text-xs">{ta.office_hours}</span>
                  )}
                </div>
              ))}
            </Section>
          )}

          {/* Grading */}
          {grading.length > 0 && (
            <Section title="Grading breakdown">
              <div className="space-y-1">
                {grading.map((g, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span className="text-gray-300">{g.component}</span>
                    <span className="text-indigo-400 font-mono">{g.weight}%</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Calendar events */}
          {events.length > 0 && (
            <Section title={`Calendar events (${events.length})`}>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {events.map((ev, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm">
                    <span className="text-gray-500 font-mono text-xs w-24 shrink-0">
                      {ev.date ?? '—'}
                    </span>
                    <span className="text-gray-300 truncate">{ev.title}</span>
                    {ev.type && (
                      <span className="text-xs text-gray-600 shrink-0">{ev.type}</span>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Schedule */}
          {schedule.length > 0 && (
            <Section title={`Course schedule (${schedule.length} weeks)`}>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {schedule.map((s, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm">
                    <span className="text-gray-500 font-mono text-xs w-16 shrink-0">
                      {s.week != null ? `Wk ${s.week}` : s.date ?? '—'}
                    </span>
                    <span className="text-gray-300 truncate">{s.topic}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {!professor && !tas.length && !grading.length && !events.length && !schedule.length && (
            <p className="text-gray-500 text-sm text-center py-8">
              No structured data was extracted — the syllabus may be image-based.
              You can still save the file.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex gap-3">
          <button
            onClick={onSkip}
            className="flex-1 py-2.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 text-sm transition-colors"
          >
            Skip for now
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            {saving ? 'Saving...' : 'Looks good — Save All'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-gray-500 text-xs font-semibold uppercase tracking-wider mb-2">
        {title}
      </h3>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

function Row({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null
  return (
    <div className="flex gap-3 text-sm">
      <span className="text-gray-600 w-28 shrink-0">{label}</span>
      <span className="text-gray-300">{value}</span>
    </div>
  )
}
