export function SidecarSplash() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 gap-6">
      <div className="flex items-center gap-3">
        <div
          className="w-5 h-5 rounded-full bg-indigo-500 animate-pulse"
          role="status"
          aria-label="Loading"
        />
        <span className="text-gray-300 text-lg font-medium tracking-wide">
          YakAI is starting up...
        </span>
      </div>
      <p className="text-gray-500 text-sm">Connecting to AI engine</p>
    </div>
  )
}
