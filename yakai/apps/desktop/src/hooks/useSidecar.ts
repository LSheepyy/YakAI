import { useEffect } from 'react'
import { useAppStore } from '../stores/appStore'
import { SIDECAR_BASE } from './useApi'

const POLL_INTERVAL_MS = 500
const TIMEOUT_MS = 15_000

export function useSidecar() {
  const setSidecarReady = useAppStore((s) => s.setSidecarReady)
  const setSidecarError = useAppStore((s) => s.setSidecarError)
  const ready = useAppStore((s) => s.sidecarReady)
  const error = useAppStore((s) => s.sidecarError)

  useEffect(() => {
    if (ready) return

    let stopped = false
    const start = Date.now()

    async function poll() {
      while (!stopped) {
        try {
          const res = await fetch(`${SIDECAR_BASE}/health`, { signal: AbortSignal.timeout(1000) })
          if (res.ok) {
            setSidecarReady(true)
            return
          }
        } catch {
          // still starting
        }
        if (Date.now() - start > TIMEOUT_MS) {
          setSidecarError('AI engine failed to start after 15 seconds.')
          return
        }
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
      }
    }

    poll()
    return () => { stopped = true }
  }, [ready, setSidecarReady, setSidecarError])

  return { ready, error }
}
