import { useState } from 'react'
import { ClassHub } from '../ClassHub/ClassHub'
import { Sidebar } from '../Sidebar/Sidebar'
import { SettingsScreen } from '../Settings/SettingsScreen'
import { useAppStore } from '../../stores/appStore'

export function MainLayout() {
  const selectedClassId = useAppStore((s) => s.selectedClassId)
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <div className="flex flex-col h-screen bg-gray-950 overflow-hidden">
      {/* Global top bar */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-gray-800 shrink-0">
        <span className="text-gray-100 font-bold text-lg tracking-tight">YakAI</span>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSettingsOpen(true)}
            className="text-gray-500 hover:text-gray-300 transition-colors text-xl leading-none"
            title="Settings"
          >
            ⚙
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden flex flex-col">
          {selectedClassId ? (
            <ClassHub classId={selectedClassId} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-gray-600 text-lg">Select a class from the sidebar</p>
                <p className="text-gray-700 text-sm mt-1">or create a new one to get started</p>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Settings overlay */}
      {settingsOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end">
          <div className="bg-gray-950 border-l border-gray-800 w-full max-w-md flex flex-col shadow-2xl">
            <SettingsScreen onClose={() => setSettingsOpen(false)} />
          </div>
        </div>
      )}
    </div>
  )
}
