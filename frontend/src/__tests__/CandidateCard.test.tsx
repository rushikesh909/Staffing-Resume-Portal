import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CandidateCard } from '../components/CandidateCard'
import { Candidate } from '@/lib/types'

describe('CandidateCard component - contact masking logic', () => {
  const sampleCandidate: Candidate = {
    id: 101,
    name: 'Priya Verma',
    email: 'priya.verma@example.com',
    phone: '+91 9876543210',
    current_role: 'Lead Java Engineer',
    experience_years: 6,
    notice_days: 30,
    ai_score: 85,
    pipeline_stage: 'client_reviewed',
  }

  it('masks contact info in client mode when stage is prior to interview', () => {
    render(
      <CandidateCard
        candidate={sampleCandidate}
        mode="client"
      />
    )

    // Should display masking message
    expect(screen.getByText('Contacts masked until interview')).toBeInTheDocument()

    // Email and phone should NOT be displayed
    expect(screen.queryByText('priya.verma@example.com')).not.toBeInTheDocument()
    expect(screen.queryByText('+91 9876543210')).not.toBeInTheDocument()
  })

  it('reveals contact info in client mode when stage is interview_scheduled', () => {
    const interviewCandidate: Candidate = {
      ...sampleCandidate,
      pipeline_stage: 'interview_scheduled',
    }

    render(
      <CandidateCard
        candidate={interviewCandidate}
        mode="client"
      />
    )

    // Should NOT show masking message
    expect(screen.queryByText('Contacts masked until interview')).not.toBeInTheDocument()

    // Email should be visible
    expect(screen.getByText('priya.verma@example.com')).toBeInTheDocument()
  })

  it('reveals contact info in client mode when stage is offer_made or joined', () => {
    const offerCandidate: Candidate = {
      ...sampleCandidate,
      pipeline_stage: 'offer_made',
    }

    render(
      <CandidateCard
        candidate={offerCandidate}
        mode="client"
      />
    )

    expect(screen.queryByText('Contacts masked until interview')).not.toBeInTheDocument()
    expect(screen.getByText('priya.verma@example.com')).toBeInTheDocument()
  })

  it('always shows contact info in recruiter mode regardless of stage', () => {
    render(
      <CandidateCard
        candidate={sampleCandidate}
        mode="recruiter"
      />
    )

    // Should NOT show masking message
    expect(screen.queryByText('Contacts masked until interview')).not.toBeInTheDocument()

    // Email should be visible
    expect(screen.getByText('priya.verma@example.com')).toBeInTheDocument()
  })
})
