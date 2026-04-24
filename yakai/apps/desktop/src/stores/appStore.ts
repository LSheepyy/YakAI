import { create } from 'zustand'
import type { Class, Semester } from '../types'

interface User {
  name: string
  major: string
  apiKey: string
}

interface AppState {
  sidecarReady: boolean
  sidecarError: string | null
  setSidecarReady: (ready: boolean) => void
  setSidecarError: (error: string | null) => void

  onboardingComplete: boolean
  setOnboardingComplete: (v: boolean) => void

  user: User | null
  setUser: (user: User | null) => void

  selectedClassId: string | null
  selectClass: (id: string | null) => void

  semesters: Semester[]
  setSemesters: (s: Semester[]) => void
  addClass: (cls: Class) => void
  updateClass: (id: string, updates: Partial<Class>) => void
  removeClass: (id: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidecarReady: false,
  sidecarError: null,
  setSidecarReady: (ready) => set({ sidecarReady: ready }),
  setSidecarError: (error) => set({ sidecarError: error }),

  onboardingComplete: false,
  setOnboardingComplete: (v) => set({ onboardingComplete: v }),

  user: null,
  setUser: (user) => set({ user }),

  selectedClassId: null,
  selectClass: (id) => set({ selectedClassId: id }),

  semesters: [],
  setSemesters: (semesters) => set({ semesters }),

  addClass: (cls) =>
    set((state) => ({
      semesters: state.semesters.map((sem) =>
        sem.id === cls.semester_id
          ? { ...sem, classes: [...sem.classes, cls] }
          : sem
      ),
    })),

  updateClass: (id, updates) =>
    set((state) => ({
      semesters: state.semesters.map((sem) => ({
        ...sem,
        classes: sem.classes.map((c) =>
          c.id === id ? { ...c, ...updates } : c
        ),
      })),
    })),

  removeClass: (id) =>
    set((state) => ({
      semesters: state.semesters.map((sem) => ({
        ...sem,
        classes: sem.classes.filter((c) => c.id !== id),
      })),
      selectedClassId: state.selectedClassId === id ? null : state.selectedClassId,
    })),
}))
