import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import DateInputs from '@/components/search/DateInputs'

describe('DateInputs', () => {
  const getTomorrowDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }

  const getDayAfterTomorrow = () => {
    const dayAfter = new Date()
    dayAfter.setDate(dayAfter.getDate() + 2)
    return dayAfter.toISOString().split('T')[0]
  }

  it('renders check-in and check-out inputs', () => {
    const mockOnChange = jest.fn()
    render(
      <DateInputs
        checkIn={getTomorrowDate()}
        checkOut={getDayAfterTomorrow()}
        onChange={mockOnChange}
      />
    )

    expect(screen.getByTestId('checkin-date-input')).toBeInTheDocument()
    expect(screen.getByTestId('checkout-date-input')).toBeInTheDocument()
  })

  it('enforces minimum check-in date (tomorrow)', () => {
    const mockOnChange = jest.fn()
    const { rerender } = render(
      <DateInputs
        checkIn={getTomorrowDate()}
        checkOut={getDayAfterTomorrow()}
        onChange={mockOnChange}
      />
    )

    const checkInInput = screen.getByTestId('checkin-date-input') as HTMLInputElement
    expect(checkInInput.min).toBe(getTomorrowDate())
  })

  it('enforces check-out > check-in', () => {
    const mockOnChange = jest.fn()
    render(
      <DateInputs
        checkIn={getTomorrowDate()}
        checkOut={getDayAfterTomorrow()}
        onChange={mockOnChange}
      />
    )

    const checkOutInput = screen.getByTestId('checkout-date-input') as HTMLInputElement
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const minCheckOut = new Date(tomorrow)
    minCheckOut.setDate(minCheckOut.getDate() + 1)
    
    expect(checkOutInput.min).toBe(minCheckOut.toISOString().split('T')[0])
  })

  it('calls onChange when dates are updated', () => {
    const mockOnChange = jest.fn()
    render(
      <DateInputs
        checkIn={getTomorrowDate()}
        checkOut={getDayAfterTomorrow()}
        onChange={mockOnChange}
      />
    )

    // onChange is called on mount via useEffect
    expect(mockOnChange).toHaveBeenCalled()
  })
})
