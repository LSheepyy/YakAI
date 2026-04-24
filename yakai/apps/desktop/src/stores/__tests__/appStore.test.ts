import { beforeEach, describe, expect, it } from 'vitest'
import { useAppStore } from '../appStore'
import type { Class, Semester } from '../../types'

function resetStore() {
  useAppStore.setState({
    sidecarReady: false,
    sidecarError: null,
    onboardingComplete: false,
    user: null,
    selectedClassId: null,
    semesters: [],
  })
}

const mockClass: Class = {
  id: 'cls-1',
  semester_id: 'sem-1',
  course_code: 'ENGR2410',
  course_name: 'Circuit Analysis',
  slug: 'engr2410-circuit-analysis',
  professor: 'Dr. Smith',
  major: 'EE',
  brain_file_path: '/path/brain.md',
  inherited_from_class_id: null,
  is_archived: 0,
  created_at: '2026-01-01T00:00:00',
}

const mockSemester: Semester = {
  id: 'sem-1',
  name: 'Fall 2026',
  user_id: 'user-1',
  classes: [],
}

describe('appStore', () => {
  beforeEach(resetStore)

  it('has correct initial state', () => {
    const state = useAppStore.getState()
    expect(state.sidecarReady).toBe(false)
    expect(state.onboardingComplete).toBe(false)
    expect(state.selectedClassId).toBeNull()
    expect(state.semesters).toEqual([])
    expect(state.user).toBeNull()
  })

  it('setSidecarReady updates state', () => {
    useAppStore.getState().setSidecarReady(true)
    expect(useAppStore.getState().sidecarReady).toBe(true)
  })

  it('setSidecarError updates state', () => {
    useAppStore.getState().setSidecarError('connection refused')
    expect(useAppStore.getState().sidecarError).toBe('connection refused')
  })

  it('setOnboardingComplete updates state', () => {
    useAppStore.getState().setOnboardingComplete(true)
    expect(useAppStore.getState().onboardingComplete).toBe(true)
  })

  it('selectClass updates selectedClassId', () => {
    useAppStore.getState().selectClass('cls-42')
    expect(useAppStore.getState().selectedClassId).toBe('cls-42')
  })

  it('selectClass can be set to null', () => {
    useAppStore.getState().selectClass('cls-1')
    useAppStore.getState().selectClass(null)
    expect(useAppStore.getState().selectedClassId).toBeNull()
  })

  it('addClass appends class to correct semester', () => {
    useAppStore.getState().setSemesters([mockSemester])
    useAppStore.getState().addClass(mockClass)
    const semesters = useAppStore.getState().semesters
    expect(semesters[0].classes).toHaveLength(1)
    expect(semesters[0].classes[0].id).toBe('cls-1')
  })

  it('addClass does not add to wrong semester', () => {
    const otherSem: Semester = { ...mockSemester, id: 'sem-other', classes: [] }
    useAppStore.getState().setSemesters([otherSem])
    useAppStore.getState().addClass(mockClass) // mockClass.semester_id = 'sem-1', not 'sem-other'
    expect(useAppStore.getState().semesters[0].classes).toHaveLength(0)
  })

  it('updateClass merges partial updates correctly', () => {
    useAppStore.getState().setSemesters([{ ...mockSemester, classes: [mockClass] }])
    useAppStore.getState().updateClass('cls-1', { professor: 'Dr. New' })
    const updated = useAppStore.getState().semesters[0].classes[0]
    expect(updated.professor).toBe('Dr. New')
    expect(updated.course_code).toBe('ENGR2410') // unchanged
  })

  it('updateClass does not affect other classes', () => {
    const cls2: Class = { ...mockClass, id: 'cls-2', course_code: 'CS101' }
    useAppStore.getState().setSemesters([{ ...mockSemester, classes: [mockClass, cls2] }])
    useAppStore.getState().updateClass('cls-1', { professor: 'Changed' })
    const cls2After = useAppStore.getState().semesters[0].classes[1]
    expect(cls2After.professor).toBe('Dr. Smith')
  })
})
