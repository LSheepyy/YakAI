import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Onboarding } from '../Onboarding'
import { useAppStore } from '../../../stores/appStore'

// Mock the API hook
vi.mock('../../../hooks/useApi', () => ({
  useApi: () => ({
    createSemester: vi.fn().mockResolvedValue({ id: 'sem-1', name: 'Fall 2026', user_id: 'u', classes: [] }),
    createClass: vi.fn().mockResolvedValue({
      id: 'cls-1', semester_id: 'sem-1', course_code: 'CS101', course_name: 'Intro',
      slug: 'cs101', professor: null, major: null, brain_file_path: null,
      inherited_from_class_id: null, is_archived: 0, created_at: '2026-01-01',
    }),
    checkHealth: vi.fn().mockResolvedValue(true),
    validateApiKey: vi.fn().mockResolvedValue(true),
  }),
}))

function resetStore() {
  useAppStore.setState({ onboardingComplete: false, user: null, semesters: [] })
}

describe('Onboarding', () => {
  beforeEach(resetStore)

  it('shows Step 1 on mount', () => {
    render(<Onboarding />)
    expect(screen.getByText('Step 1 of 4')).toBeInTheDocument()
    expect(screen.getByText(/what's your name/i)).toBeInTheDocument()
  })

  it('shows error when advancing without a name', async () => {
    render(<Onboarding />)
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
  })

  it('advances to step 2 after entering a name', async () => {
    render(<Onboarding />)
    await userEvent.type(screen.getByPlaceholderText(/your name/i), 'Avery')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    expect(await screen.findByText('Step 2 of 4')).toBeInTheDocument()
  })

  it('back button returns to step 1 from step 2', async () => {
    render(<Onboarding />)
    await userEvent.type(screen.getByPlaceholderText(/your name/i), 'Avery')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await screen.findByText('Step 2 of 4')
    fireEvent.click(screen.getByRole('button', { name: /back/i }))
    expect(await screen.findByText('Step 1 of 4')).toBeInTheDocument()
  })

  it('shows API key input on step 3', async () => {
    render(<Onboarding />)
    // Step 1
    await userEvent.type(screen.getByPlaceholderText(/your name/i), 'Avery')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    // Step 2
    await userEvent.type(await screen.findByPlaceholderText(/electrical engineering/i), 'EE')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    // Step 3
    expect(await screen.findByText('Step 3 of 4')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/sk-/i)).toBeInTheDocument()
  })

  it('shows error for invalid API key format', async () => {
    render(<Onboarding />)
    await userEvent.type(screen.getByPlaceholderText(/your name/i), 'Avery')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await userEvent.type(await screen.findByPlaceholderText(/electrical engineering/i), 'EE')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await screen.findByText('Step 3 of 4')
    await userEvent.type(screen.getByPlaceholderText(/sk-/i), 'invalid-key')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    expect(await screen.findByText(/must start with sk-/i)).toBeInTheDocument()
  })

  it('valid sk- key advances to step 4 after validation', async () => {
    render(<Onboarding />)
    await userEvent.type(screen.getByPlaceholderText(/your name/i), 'Avery')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await userEvent.type(await screen.findByPlaceholderText(/electrical engineering/i), 'EE')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await screen.findByText('Step 3 of 4')
    await userEvent.type(screen.getByPlaceholderText(/sk-/i), 'sk-test-key-12345')
    // Click "Validate Key" first, then "Next"
    fireEvent.click(screen.getByRole('button', { name: /validate key/i }))
    expect(await screen.findByText(/verified/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    expect(await screen.findByText('Step 4 of 4')).toBeInTheDocument()
  })
})
