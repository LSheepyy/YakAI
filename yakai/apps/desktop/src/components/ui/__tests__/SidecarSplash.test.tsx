import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SidecarSplash } from '../SidecarSplash'

describe('SidecarSplash', () => {
  it('renders the startup message', () => {
    render(<SidecarSplash />)
    expect(screen.getByText(/YakAI is starting up/i)).toBeInTheDocument()
  })

  it('has a loading indicator element', () => {
    render(<SidecarSplash />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders connecting text', () => {
    render(<SidecarSplash />)
    expect(screen.getByText(/Connecting to AI engine/i)).toBeInTheDocument()
  })
})
