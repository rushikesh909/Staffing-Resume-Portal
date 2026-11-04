import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ScoreCard } from '../components/ScoreCard'
import { ScoreBadge } from '../components/ui/Badge'

describe('ScoreCard and ScoreBadge component', () => {
  it('renders green badge for high score (>= 70)', () => {
    const { container } = render(<ScoreCard score={85} />)
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('Match Score')).toBeInTheDocument()
    
    // Emerald styling for >= 70
    const badge = container.querySelector('.bg-emerald-50')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('text-emerald-700')
  })

  it('renders amber badge for moderate score (40 to 69)', () => {
    const { container } = render(<ScoreCard score={55} />)
    expect(screen.getByText('55')).toBeInTheDocument()
    
    // Amber styling for 40-69
    const badge = container.querySelector('.bg-amber-50')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('text-amber-700')
  })

  it('renders red/rose badge for low score (< 40)', () => {
    const { container } = render(<ScoreCard score={25} />)
    expect(screen.getByText('25')).toBeInTheDocument()
    
    // Rose/Red styling for < 40
    const badge = container.querySelector('.bg-rose-50')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('text-rose-700')
  })

  it('renders N/A when score is null or undefined', () => {
    render(<ScoreBadge score={null} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('renders evidence quotes when provided', () => {
    const mockEvidence = {
      java: {
        evidence_lines: ['5 years of enterprise Java microservices'],
        matched: true,
      },
    }
    render(<ScoreCard score={80} evidence={mockEvidence as any} />)
    expect(screen.getByText(/5 years of enterprise Java microservices/i)).toBeInTheDocument()
  })
})
