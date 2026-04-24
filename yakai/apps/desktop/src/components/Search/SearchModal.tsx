import { useEffect, useRef, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { SearchResult } from '../../types'

interface Props {
  classId: string
  onClose: () => void
}

type FilterType = 'all' | 'semantic' | 'keyword' | 'exam-flagged'

const FILTERS: { label: string; value: FilterType }[] = [
  { label: 'All', value: 'all' },
  { label: 'Semantic', value: 'semantic' },
  { label: 'Keyword', value: 'keyword' },
  { label: 'Exam-Flagged', value: 'exam-flagged' },
]

const FILE_TYPE_ICON: Record<string, string> = {
  pdf: '📄',
  video: '🎥',
  audio: '🎙',
  image: '🖼',
  slides: '📊',
  youtube: '▶️',
  homework: '📝',
  syllabus: '📋',
  'past-exam': '📃',
  notes: '📓',
}

export function SearchModal({ classId, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<FilterType>('all')
  const [results, setResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const api = useApi()

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query.trim()) { setResults([]); return }
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const filterVal = filter === 'all' ? undefined : filter
        const data = await api.searchClass(classId, query, filterVal)
        setResults(data.results)
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, filter, classId])

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-start justify-center pt-24 z-50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800">
          <span className="text-gray-500">🔍</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search class materials..."
            className="flex-1 bg-transparent text-gray-100 text-sm placeholder-gray-600 focus:outline-none"
          />
          <button onClick={onClose} className="text-gray-600 hover:text-gray-400 text-lg leading-none">✕</button>
        </div>

        {/* Filter pills */}
        <div className="flex gap-2 px-4 py-2 border-b border-gray-800">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                filter === f.value
                  ? 'bg-indigo-600 border-indigo-500 text-white'
                  : 'border-gray-700 text-gray-500 hover:border-gray-600 hover:text-gray-400'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-y-auto">
          {searching && (
            <div className="flex justify-center py-8">
              <div className="w-4 h-4 rounded-full bg-indigo-500 animate-pulse" />
            </div>
          )}
          {!searching && query && results.length === 0 && (
            <p className="text-gray-600 text-sm text-center py-8">
              No results found. Try a different query.
            </p>
          )}
          {!searching && results.map((r, i) => (
            <div key={i} className="px-4 py-3 border-b border-gray-800 last:border-0 hover:bg-gray-800/50 transition-colors">
              <div className="flex items-start gap-2">
                <span className="text-base mt-0.5">{FILE_TYPE_ICON[r.file_type] ?? '📄'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-200 text-sm font-medium truncate">{r.source_name}</p>
                  <p className="text-gray-500 text-xs mt-0.5 line-clamp-2">{r.excerpt}</p>
                  {/* Relevance bar */}
                  <div className="flex items-center gap-2 mt-1.5">
                    <div className="flex-1 bg-gray-800 rounded-full h-1">
                      <div
                        className="bg-indigo-500 h-1 rounded-full"
                        style={{ width: `${Math.round(r.relevance_score * 100)}%` }}
                      />
                    </div>
                    <span className="text-gray-600 text-xs">{Math.round(r.relevance_score * 100)}%</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
