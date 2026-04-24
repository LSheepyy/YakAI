import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Sidebar } from '../Sidebar'
import { useAppStore } from '../../../stores/appStore'
import type { Semester } from '../../../types'

vi.mock('../../../hooks/useApi', () => ({
  useApi: () => ({
    createSemester: vi.fn(),
    createClass: vi.fn(),
  }),
}))

const mockSemester: Semester = {
  id: 'sem-1',
  name: 'Fall 2026',
  user_id: 'user-1',
  classes: [
    {
      id: 'cls-1',
      semester_id: 'sem-1',
      course_code: 'ENGR2410',
      course_name: 'Circuit Analysis',
      slug: 'engr2410',
      professor: 'Dr. Smith',
      major: null,
      brain_file_path: null,
      inherited_from_class_id: null,
      is_archived: 0,
      created_at: '2026-01-01',
    },
    {
      id: 'cls-2',
      semester_id: 'sem-1',
      course_code: 'MATH2210',
      course_name: 'Calculus III',
      slug: 'math2210',
      professor: null,
      major: null,
      brain_file_path: null,
      inherited_from_class_id: null,
      is_archived: 0,
      created_at: '2026-01-02',
    },
  ],
}

function resetStore() {
  useAppStore.setState({ semesters: [], selectedClassId: null })
}

describe('Sidebar', () => {
  beforeEach(resetStore)

  it('renders the New Class button', () => {
    render(<Sidebar />)
    expect(screen.getByText('+ New Class')).toBeInTheDocument()
  })

  it('renders semester name when store has data', () => {
    useAppStore.setState({ semesters: [mockSemester] })
    render(<Sidebar />)
    expect(screen.getByText('Fall 2026')).toBeInTheDocument()
  })

  it('renders class course codes', () => {
    useAppStore.setState({ semesters: [mockSemester] })
    render(<Sidebar />)
    expect(screen.getByText('ENGR2410')).toBeInTheDocument()
    expect(screen.getByText('MATH2210')).toBeInTheDocument()
  })

  it('clicking a class calls selectClass', () => {
    useAppStore.setState({ semesters: [mockSemester] })
    render(<Sidebar />)
    fireEvent.click(screen.getByText('ENGR2410'))
    expect(useAppStore.getState().selectedClassId).toBe('cls-1')
  })

  it('selected class has aria-selected=true', () => {
    useAppStore.setState({ semesters: [mockSemester], selectedClassId: 'cls-1' })
    render(<Sidebar />)
    const buttons = screen.getAllByRole('button')
    const selected = buttons.find((b) => b.getAttribute('aria-selected') === 'true')
    expect(selected).toBeDefined()
    expect(selected?.textContent).toContain('ENGR2410')
  })

  it('shows empty message when no classes', () => {
    render(<Sidebar />)
    expect(screen.getByText(/no classes yet/i)).toBeInTheDocument()
  })

  it('clicking New Class opens modal', () => {
    render(<Sidebar />)
    fireEvent.click(screen.getByText('+ New Class'))
    expect(screen.getByText('New Class')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/course code/i)).toBeInTheDocument()
  })
})
