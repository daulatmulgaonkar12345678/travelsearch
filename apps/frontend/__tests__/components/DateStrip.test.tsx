import { render, screen, fireEvent } from '@testing-library/react'
import DateStrip from '@/components/search/DateStrip'

describe('DateStrip', () => {
  const mockOnDateSelect = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders 7 dates by default', () => {
    render(<DateStrip onDateSelect={mockOnDateSelect} />)
    
    const today = new Date()
    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      const dateStr = date.toISOString().split('T')[0]
      expect(screen.getByTestId(`date-${dateStr}`)).toBeInTheDocument()
    }
  })

  it('calls onDateSelect when date is clicked', () => {
    render(<DateStrip onDateSelect={mockOnDateSelect} />)
    
    const today = new Date().toISOString().split('T')[0]
    const dateButton = screen.getByTestId(`date-${today}`)
    fireEvent.click(dateButton)
    
    expect(mockOnDateSelect).toHaveBeenCalledWith(today)
  })

  it('highlights cheapest date', () => {
    const priceData = {
      '2025-12-15': 5000,
      '2025-12-16': 3000, // cheapest
      '2025-12-17': 4500,
    }
    render(<DateStrip onDateSelect={mockOnDateSelect} priceData={priceData} />)
    
    // Check that cheapest date indicator is shown
    expect(screen.getByText(/Cheapest:/)).toBeInTheDocument()
  })

  it('toggles between week and month view', () => {
    render(<DateStrip onDateSelect={mockOnDateSelect} />)
    
    const toggleButton = screen.getByTestId('toggle-month-view')
    expect(toggleButton).toHaveTextContent('Show Full Month')
    
    fireEvent.click(toggleButton)
    expect(toggleButton).toHaveTextContent('Show Week')
  })

  it('displays price for each date', () => {
    const priceData = {
      '2025-12-15': 5000,
    }
    render(<DateStrip onDateSelect={mockOnDateSelect} priceData={priceData} />)
    
    expect(screen.getByText(/₹5,000/)).toBeInTheDocument()
  })
})
