import { useAppStore } from './stores/appStore'
import { useSidecar } from './hooks/useSidecar'
import { SidecarSplash } from './components/ui/SidecarSplash'
import { SidecarError } from './components/ui/SidecarError'
import { Onboarding } from './components/Onboarding/Onboarding'
import { MainLayout } from './components/ui/MainLayout'

export function App() {
  const { ready, error } = useSidecar()
  const onboardingComplete = useAppStore((s) => s.onboardingComplete)
  const setSidecarReady = useAppStore((s) => s.setSidecarReady)
  const setSidecarError = useAppStore((s) => s.setSidecarError)

  if (!ready && !error) return <SidecarSplash />

  if (error) {
    return (
      <SidecarError
        message={error}
        onRetry={() => {
          setSidecarError(null)
          setSidecarReady(false)
        }}
      />
    )
  }

  if (!onboardingComplete) return <Onboarding />

  return <MainLayout />
}
