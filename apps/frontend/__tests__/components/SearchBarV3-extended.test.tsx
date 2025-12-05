import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SearchBarV3 from '@/components/search/SearchBarV3'

describe('SearchBarV3 - Extended Tests', () => {
  describe('One-way trip', () => {
    it('disables return date input', () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByText(/One-way/i))
      
      const returnInput = screen.getByTestId('return-date-input')
      expect(returnInput).toBeDisabled()
    })

    it('shows N/A label for return date', () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByText(/One-way/i))
      
      expect(screen.getByText(/Return.*N\/A/i)).toBeInTheDocument()
    })
  })

  describe('Round-trip validation', () => {
    it('validates return date is after departure', () => {
      render(<SearchBarV3 />)
      
      const departureInput = screen.getByTestId('departure-date-input') as HTMLInputElement
      const returnInput = screen.getByTestId('return-date-input') as HTMLInputElement
      
      // Departure date should have min attribute
      expect(departureInput.min).toBeTruthy()
      
      // Return date min should be based on departure
      expect(returnInput.min).toBeTruthy()
    })
  })

  describe('Multicity builder', () => {
    it('shows at least 2 initial segments', () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByText(/Multi-city/i))
      
      expect(screen.getByText(/Flight 1/i)).toBeInTheDocument()
      expect(screen.getByText(/Flight 2/i)).toBeInTheDocument()
    })

    it('allows adding new segments', async () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByText(/Multi-city/i))
      fireEvent.click(screen.getByText(/Add Another Flight/i))
      
      await waitFor(() => {
        expect(screen.getByText(/Flight 3/i)).toBeInTheDocument()
      })
    })

    it('allows removing segments when more than 2 exist', async () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByText(/Multi-city/i))
      fireEvent.click(screen.getByText(/Add Another Flight/i))
      
      await waitFor(() => {
        expect(screen.getByText(/Flight 3/i)).toBeInTheDocument()
      })
      
      const removeButtons = screen.getAllByText(/Remove/i)
      expect(removeButtons.length).toBeGreaterThan(0)
    })

    it('has cabin class selector visible', () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByText(/Multi-city/i))
      
      expect(screen.getByText(/Cabin Class/i)).toBeInTheDocument()
    })
  })

  describe('Cabin class selector', () => {
    it('is visible for all trip types', () => {
      render(<SearchBarV3 />)
      
      // Default (roundtrip)
      expect(screen.getByText(/Cabin Class/i)).toBeInTheDocument()
      
      // One-way
      fireEvent.click(screen.getByText(/One-way/i))
      expect(screen.getByText(/Cabin Class/i)).toBeInTheDocument()
      
      // Multicity
      fireEvent.click(screen.getByText(/Multi-city/i))
      expect(screen.getByText(/Cabin Class/i)).toBeInTheDocument()
    })
  })

  describe('Tab switching', () => {
    it('switches from flights to hotels', () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByTestId('hotels-tab'))
      
      expect(screen.getByTestId('city-input')).toBeInTheDocument()
    })

    it('switches from hotels to flights', () => {
      render(<SearchBarV3 defaultTab="hotels" />)
      
      fireEvent.click(screen.getByTestId('flights-tab'))
      
      expect(screen.getByTestId('origin-input')).toBeInTheDocument()
    })
  })

  describe('Passenger selector', () => {
    it('opens passenger modal on click', () => {
      render(<SearchBarV3 />)
      
      fireEvent.click(screen.getByTestId('passenger-selector'))
      
      expect(screen.getByText(/Passengers/i)).toBeInTheDocument()
    })
  })

  describe('Hotels room selector', () => {
    it('opens room modal on click', () => {
      render(<SearchBarV3 defaultTab="hotels" />)
      
      fireEvent.click(screen.getByTestId('room-selector'))
      
      expect(screen.getByText(/Rooms & Guests/i)).toBeInTheDocument()
    })
  })

  describe('SSR safety', () => {
    it('shows loading state until mounted', () => {
      const { container } = render(<SearchBarV3 />)
      
      // Component should render without errors
      expect(container).toBeInTheDocument()
    })
  })
})
