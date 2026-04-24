import { useState } from 'react'
import type { ProfessorInfo, TAInfo } from '../../types'

interface Props {
  professor: ProfessorInfo
  tas: TAInfo[]
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }
  return (
    <button
      onClick={copy}
      className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors ml-2"
    >
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

export function ProfessorCard({ professor, tas }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Professor</h3>
      <p className="text-gray-100 font-semibold text-lg">{professor.name}</p>
      {professor.email && (
        <div className="flex items-center gap-1 mt-1">
          <span className="text-gray-400 text-sm">{professor.email}</span>
          <CopyButton text={professor.email} />
        </div>
      )}
      {professor.office_location && (
        <p className="text-gray-500 text-sm mt-1">{professor.office_location}</p>
      )}
      {professor.office_hours && (
        <p className="text-gray-500 text-sm">Office hours: {professor.office_hours}</p>
      )}
      {tas.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">TAs</p>
          {tas.map((ta) => (
            <div key={ta.id} className="flex items-center gap-2 text-sm text-gray-400">
              <span>{ta.name}</span>
              {ta.email && (
                <>
                  <span className="text-gray-600">·</span>
                  <span>{ta.email}</span>
                  <CopyButton text={ta.email} />
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
