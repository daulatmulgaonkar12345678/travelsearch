import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AirportAutocomplete from '@/components/search/AirportAutocomplete'

global.fetch = jest.fn()

describe('AirportAutocomplete', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders input field', () => {
    const mockOnChange = jest.fn()
    render(
      <AirportAutocomplete
        value=""
        onChange={mockOnChange}
        placeholder="Search airports"
      />
    )

    expect(screen.getByPlaceholderText('Search airports')).toBeInTheDocument()
  })

  it('does not fetch for queries < 2 characters', async () => {
    const mockOnChange = jest.fn()
    render(
      <AirportAutocomplete
        value=""
        onChange={mockOnChange}
      />
    )

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'p' } })

    await waitFor(() => {
      expect(fetch).not.toHaveBeenCalled()
    })
  })

  it('fetches suggestions for valid queries', async () => {
    const mockOnChange = jest.fn()
    const mockAirports = [
      { iata: 'PNQ', name: 'Pune Airport', city: 'Pune', country: 'India' }
    ]

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAirports
    })

    render(
      <AirportAutocomplete
        value=""
        onChange={mockOnChange}
      />
    )

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'pu' } })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/airports?query=pu')
      )
    }, { timeout: 1000 })
  })

  it('calls onChange with IATA code when airport selected', async () => {
    const mockOnChange = jest.fn()
    const mockAirports = [
      { iata: 'PNQ', name: 'Pune Airport', city: 'Pune', country: 'India' }
    ]

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAirports
    })

    render(
      <AirportAutocomplete
        value=""
        onChange={mockOnChange}
      />
    )

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'pune' } })
    fireEvent.focus(input)

    await waitFor(() => {
      expect(screen.getByText(/Pune, India/)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText(/Pune, India/))

    expect(mockOnChange).toHaveBeenCalledWith('PNQ', mockAirports[0])
  })
})
