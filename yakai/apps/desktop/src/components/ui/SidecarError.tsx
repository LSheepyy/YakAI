interface Props {
  message: string | null
  onRetry: () => void
}

export function SidecarError({ message, onRetry }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 gap-4">
      <div className="bg-gray-900 border border-red-800 rounded-xl p-8 max-w-md w-full mx-4">
        <h2 className="text-red-400 text-lg font-semibold mb-2">AI engine failed to start</h2>
        {message && (
          <p className="text-gray-400 text-sm mb-4 font-mono bg-gray-950 p-3 rounded-lg break-all">
            {message}
          </p>
        )}
        <p className="text-gray-500 text-sm mb-6">
          Check that Python is installed and no other process is using port 8765.
        </p>
        <button
          onClick={onRetry}
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          Restart AI
        </button>
      </div>
    </div>
  )
}
