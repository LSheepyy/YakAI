import { ClassHub } from '../ClassHub/ClassHub'
import { Sidebar } from '../Sidebar/Sidebar'
import { useAppStore } from '../../stores/appStore'

export function MainLayout() {
  const selectedClassId = useAppStore((s) => s.selectedClassId)

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
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
  )
}
