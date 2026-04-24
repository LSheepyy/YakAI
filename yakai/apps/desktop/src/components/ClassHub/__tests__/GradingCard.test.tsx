import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { GradingCard } from '../GradingCard'
import type { GradingWeight } from '../../../types'

const weights: GradingWeight[] = [
  { id: 'gw-1', class_id: 'cls-1', component: 'Assignments', weight_pct: 20 },
  { id: 'gw-2', class_id: 'cls-1', component: 'Midterm', weight_pct: 30 },
  { id: 'gw-3', class_id: 'cls-1', component: 'Final', weight_pct: 40 },
  { id: 'gw-4', class_id: 'cls-1', component: 'Quizzes', weight_pct: 10 },
]

describe('GradingCard', () => {
  it('displays all component names', () => {
    render(<GradingCard weights={weights} />)
    expect(screen.getByText('Assignments')).toBeInTheDocument()
    expect(screen.getByText('Midterm')).toBeInTheDocument()
    expect(screen.getByText('Final')).toBeInTheDocument()
    expect(screen.getByText('Quizzes')).toBeInTheDocument()
  })

  it('displays percentages', () => {
    render(<GradingCard weights={weights} />)
    expect(screen.getByText('20%')).toBeInTheDocument()
    expect(screen.getByText('30%')).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()
    expect(screen.getByText('10%')).toBeInTheDocument()
  })

  it('renders a visual bar', () => {
    render(<GradingCard weights={weights} />)
    // The bar divs are inside a flex container
    const bars = document.querySelectorAll('[title]')
    expect(bars.length).toBe(4)
  })

  it('renders with single weight', () => {
    render(<GradingCard weights={[{ id: 'gw-1', class_id: 'cls-1', component: 'Final', weight_pct: 100 }]} />)
    expect(screen.getByText('Final')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })
})
