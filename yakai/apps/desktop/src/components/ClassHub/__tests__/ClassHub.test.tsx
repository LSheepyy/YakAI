import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ClassHub } from '../ClassHub'
import type { ClassDetail } from '../../../types'

const mockClassDetail: ClassDetail = {
  id: 'cls-1',
  semester_id: 'sem-1',
  course_code: 'ENGR2410',
  course_name: 'Circuit Analysis',
  slug: 'engr2410',
  professor: 'Dr. Smith',
  major: 'EE',
  brain_file_path: '/path/brain.md',
  inherited_from_class_id: null,
  is_archived: 0,
  created_at: '2026-01-01',
  professor_info: null,
  ta_info: [],
  grading_weights: [],
  lectures: [],
  required_materials: [],
}

const mockGetClass = vi.fn().mockResolvedValue(mockClassDetail)
const mockIngestFile = vi.fn()

vi.mock('../../../hooks/useApi', () => ({
  useApi: () => ({
    getClass: mockGetClass,
    ingestFile: mockIngestFile,
  }),
}))

describe('ClassHub', () => {
  beforeEach(() => {
    mockGetClass.mockResolvedValue(mockClassDetail)
  })

  it('shows loading state initially', () => {
    render(<ClassHub classId="cls-1" />)
    // Loading pulse is rendered before data arrives
    const pulse = document.querySelector('.animate-pulse')
    expect(pulse).toBeTruthy()
  })

  it('renders class header after load', async () => {
    render(<ClassHub classId="cls-1" />)
    expect(await screen.findByText(/ENGR2410 — Circuit Analysis/)).toBeInTheDocument()
  })

  it('shows no-syllabus banner when professor_info is null', async () => {
    render(<ClassHub classId="cls-1" />)
    expect(await screen.findByText(/No syllabus added yet/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Add Syllabus/i })).toBeInTheDocument()
  })

  it('shows ProfessorCard when professor_info is present', async () => {
    mockGetClass.mockResolvedValueOnce({
      ...mockClassDetail,
      professor_info: {
        id: 'prof-1', class_id: 'cls-1', name: 'Dr. Sarah Smith',
        email: 'smith@uni.edu', phone: null, office_location: 'ENG 214',
        office_hours: 'Tue/Thu 2-4pm', department: null,
      },
    })
    render(<ClassHub classId="cls-1" />)
    expect(await screen.findByText('Dr. Sarah Smith')).toBeInTheDocument()
    expect(screen.getByText('smith@uni.edu')).toBeInTheDocument()
  })

  it('shows GradingCard when grading weights present', async () => {
    mockGetClass.mockResolvedValueOnce({
      ...mockClassDetail,
      professor_info: {
        id: 'p1', class_id: 'cls-1', name: 'Dr. X',
        email: null, phone: null, office_location: null, office_hours: null, department: null,
      },
      grading_weights: [
        { id: 'gw-1', class_id: 'cls-1', component: 'Midterm', weight_pct: 30 },
        { id: 'gw-2', class_id: 'cls-1', component: 'Final', weight_pct: 40 },
      ],
    })
    render(<ClassHub classId="cls-1" />)
    expect(await screen.findByText('Midterm')).toBeInTheDocument()
    expect(screen.getByText('Final')).toBeInTheDocument()
  })

  it('renders file drop zone', async () => {
    render(<ClassHub classId="cls-1" />)
    await screen.findByText(/ENGR2410/)
    expect(screen.getByRole('button', { name: /drop files here/i })).toBeInTheDocument()
  })

  it('shows error state when API fails', async () => {
    mockGetClass.mockRejectedValueOnce(new Error('Network error'))
    render(<ClassHub classId="cls-1" />)
    expect(await screen.findByText(/Failed to load class/i)).toBeInTheDocument()
  })
})
