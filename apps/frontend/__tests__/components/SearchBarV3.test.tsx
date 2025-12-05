import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import SearchBarV3 from '@/components/search/SearchBarV3'

describe('SearchBarV3', () => {
  it('renders flights tab by default', () => {
    render(<SearchBarV3 />)
    expect(screen.getByTestId('flights-tab')).toHaveClass('text-blue-600')
  })

  it('renders hotels tab when defaultTab is hotels', () => {
    render(<SearchBarV3 defaultTab="hotels" />)
    expect(screen.getByTestId('hotels-tab')).toHaveClass('text-blue-600')
  })

  it('switches between tabs', () => {
    render(<SearchBarV3 />)
    
    const hotelsTab = screen.getByTestId('hotels-tab')
    fireEvent.click(hotelsTab)
    
    expect(screen.getByTestId('city-input')).toBeInTheDocument()
  })

  it('shows cabin class selector for all trip types', () => {
    render(<SearchBarV3 />)
    
    // Should show cabin class selector
    expect(screen.getByText(/Cabin Class/i)).toBeInTheDocument()
  })

  it('disables return date for one-way trips', () => {
    render(<SearchBarV3 />)
    
    // Click one-way button
    fireEvent.click(screen.getByText(/One-way/i))
    
    const returnDateInput = screen.getByTestId('return-date-input')
    expect(returnDateInput).toBeDisabled()
  })

  it('validates departure date minimum (tomorrow)', () => {
    render(<SearchBarV3 />)
    
    const departureInput = screen.getByTestId('departure-date-input') as HTMLInputElement
    
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const minDate = tomorrow.toISOString().split('T')[0]
    
    expect(departureInput.min).toBe(minDate)
  })

  it('shows multicity builder when multicity selected', () => {
    render(<SearchBarV3 />)
    
    fireEvent.click(screen.getByText(/Multi-city/i))
    
    expect(screen.getByText(/Flight 1/i)).toBeInTheDocument()
    expect(screen.getByText(/Flight 2/i)).toBeInTheDocument()
  })

  it('multicity has cabin class selector', () => {
    render(<SearchBarV3 />)
    
    fireEvent.click(screen.getByText(/Multi-city/i))
    
    // Cabin class should still be visible
    expect(screen.getByText(/Cabin Class/i)).toBeInTheDocument()
  })
})
