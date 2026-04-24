import { useRef, useState } from 'react'
import { useAppStore } from '../../stores/appStore'
import { useApi } from '../../hooks/useApi'
import { CreateClassModal } from './CreateClassModal'
import type { Class } from '../../types'

interface DeleteModalProps {
  cls: Class
  onConfirm: () => Promise<void>
  onCancel: () => void
}

function DeleteClassModal({ cls, onConfirm, onCancel }: DeleteModalProps) {
  const [input, setInput] = useState('')
  const [deleting, setDeleting] = useState(false)

  async function handleConfirm() {
    setDeleting(true)
    await onConfirm()
    setDeleting(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
        <h2 className="text-gray-100 font-bold text-lg mb-2">Delete class?</h2>
        <p className="text-gray-400 text-sm mb-4">
          This permanently removes the BRAIN file and all SQLite records for{' '}
          <span className="text-white font-mono">{cls.course_code}</span>. This cannot be undone.
        </p>
        <p className="text-gray-500 text-xs mb-2">
          Type <span className="text-white font-mono">{cls.course_code}</span> to confirm:
        </p>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm font-mono focus:outline-none focus:border-red-500 mb-4"
          autoFocus
        />
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="flex-1 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={input !== cls.course_code || deleting}
            className="flex-1 py-2 rounded-lg bg-red-700 hover:bg-red-600 disabled:opacity-40 text-white text-sm font-medium transition-colors"
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Sidebar() {
  const semesters = useAppStore((s) => s.semesters)
  const selectedClassId = useAppStore((s) => s.selectedClassId)
  const selectClass = useAppStore((s) => s.selectClass)
  const updateClass = useAppStore((s) => s.updateClass)
  const removeClass = useAppStore((s) => s.removeClass)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [showModal, setShowModal] = useState(false)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [deletingClass, setDeletingClass] = useState<Class | null>(null)
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const renameInputRef = useRef<HTMLInputElement>(null)
  const api = useApi()

  function toggleSemester(id: string) {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function startRename(cls: Class, e: React.MouseEvent) {
    e.stopPropagation()
    setRenamingId(cls.id)
    setRenameValue(cls.course_name)
    setTimeout(() => renameInputRef.current?.select(), 0)
  }

  async function commitRename(cls: Class) {
    const trimmed = renameValue.trim()
    if (trimmed && trimmed !== cls.course_name) {
      const updated = await api.renameClass(cls.id, trimmed)
      updateClass(cls.id, { course_name: updated.course_name })
    }
    setRenamingId(null)
  }

  function handleRenameKey(e: React.KeyboardEvent, cls: Class) {
    if (e.key === 'Enter') commitRename(cls)
    if (e.key === 'Escape') setRenamingId(null)
  }

  async function handleDeleteConfirm() {
    if (!deletingClass) return
    await api.deleteClass(deletingClass.id)
    removeClass(deletingClass.id)
    setDeletingClass(null)
  }

  return (
    <>
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
        <div className="p-4 border-b border-gray-800">
          <span className="text-gray-100 font-bold text-lg tracking-tight">YakAI</span>
        </div>

        <nav className="flex-1 overflow-y-auto p-2">
          {semesters.map((sem) => (
            <div key={sem.id} className="mb-1">
              <button
                onClick={() => toggleSemester(sem.id)}
                className="w-full text-left px-3 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors flex items-center gap-1"
              >
                <span>{collapsed.has(sem.id) ? '▶' : '▼'}</span>
                {sem.name}
              </button>
              {!collapsed.has(sem.id) && (
                <div className="ml-2">
                  {sem.classes.filter((c) => !c.is_archived).map((cls) => (
                    <div
                      key={cls.id}
                      className="relative mb-0.5"
                      onMouseEnter={() => setHoveredId(cls.id)}
                      onMouseLeave={() => setHoveredId(null)}
                    >
                      {renamingId === cls.id ? (
                        <input
                          ref={renameInputRef}
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onBlur={() => commitRename(cls)}
                          onKeyDown={(e) => handleRenameKey(e, cls)}
                          className="w-full bg-gray-800 border border-indigo-500 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <button
                          onClick={() => selectClass(cls.id)}
                          aria-selected={selectedClassId === cls.id}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                            selectedClassId === cls.id
                              ? 'bg-indigo-600 text-white'
                              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                          }`}
                        >
                          <span className="font-medium">{cls.course_code}</span>
                          <span className="text-xs block opacity-75 truncate pr-10">
                            {cls.course_name}
                          </span>
                        </button>
                      )}

                      {hoveredId === cls.id && renamingId !== cls.id && (
                        <div className="absolute right-1 top-1/2 -translate-y-1/2 flex gap-0.5">
                          <button
                            onClick={(e) => startRename(cls, e)}
                            title="Rename"
                            className="p-1 text-gray-500 hover:text-gray-200 rounded transition-colors"
                          >
                            ✏
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); setDeletingClass(cls) }}
                            title="Delete"
                            className="p-1 text-gray-500 hover:text-red-400 rounded transition-colors"
                          >
                            🗑
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {semesters.length === 0 && (
            <p className="text-gray-600 text-xs px-3 py-2">No classes yet</p>
          )}
        </nav>

        <div className="p-2 border-t border-gray-800 space-y-1">
          <button
            onClick={() => setShowModal(true)}
            className="w-full text-left px-3 py-2 text-sm text-indigo-400 hover:bg-gray-800 rounded-lg transition-colors"
          >
            + New Class
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-800 rounded-lg transition-colors">
            📅 Calendar
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-800 rounded-lg transition-colors">
            💾 Backup
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:bg-gray-800 rounded-lg transition-colors">
            ⚙ Settings
          </button>
        </div>
      </aside>

      {showModal && <CreateClassModal onClose={() => setShowModal(false)} />}

      {deletingClass && (
        <DeleteClassModal
          cls={deletingClass}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeletingClass(null)}
        />
      )}
    </>
  )
}
