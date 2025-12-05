import { render, screen, fireEvent } from '@testing-library/react'
import ResultCard from '@/components/results/ResultCard'

const mockOffer = {
  offer_id: 'TEST-001',
  provider: 'test-provider',
  price: 5000,
  currency: 'INR',
  segments: [
    {
      departure_airport: 'BOM',
      arrival_airport: 'PNQ',
      departure_time: '2025-12-15T10:00:00',
      arrival_time: '2025-12-15T11:30:00',
      carrier_code: '6E',
      carrier_name: 'IndiGo',
      flight_number: '6E-123',
      duration_minutes: 90,
    },
  ],
  total_duration_minutes: 90,
  stops: 0,
  providers: [
    {
      name: 'Provider A',
      price: 5000,
      deep_link: 'https://test.com',
      rating: 85,
    },
  ],
}

describe('ResultCard', () => {
  const mockOnProviderSelect = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders flight details correctly', () => {
    render(<ResultCard offer={mockOffer} onProviderSelect={mockOnProviderSelect} />)
    
    expect(screen.getByText('IndiGo')).toBeInTheDocument()
    expect(screen.getByText(/BOM/)).toBeInTheDocument()
    expect(screen.getByText(/PNQ/)).toBeInTheDocument()
    expect(screen.getByText(/Non-stop/)).toBeInTheDocument()
  })

  it('displays price correctly', () => {
    render(<ResultCard offer={mockOffer} onProviderSelect={mockOnProviderSelect} />)
    
    expect(screen.getByText(/₹5,000/)).toBeInTheDocument()
  })

  it('shows provider offers', () => {
    render(<ResultCard offer={mockOffer} onProviderSelect={mockOnProviderSelect} />)
    
    expect(screen.getByTestId('provider-card-Provider A')).toBeInTheDocument()
  })

  it('displays badge when provided', () => {
    render(<ResultCard offer={mockOffer} badge="best" onProviderSelect={mockOnProviderSelect} />)
    
    expect(screen.getByText('Best Value')).toBeInTheDocument()
  })

  it('shows layover info for multi-segment flights', () => {
    const multiSegmentOffer = {
      ...mockOffer,
      stops: 1,
      segments: [
        { ...mockOffer.segments[0], arrival_time: '2025-12-15T11:00:00' },
        {
          ...mockOffer.segments[0],
          departure_airport: 'DEL',
          departure_time: '2025-12-15T13:00:00',
          arrival_time: '2025-12-15T14:30:00',
        },
      ],
    }
    
    render(<ResultCard offer={multiSegmentOffer} onProviderSelect={mockOnProviderSelect} />)
    
    expect(screen.getByText(/Layovers:/)).toBeInTheDocument()
  })

  it('expands provider list when show all clicked', () => {
    const offerWithMultipleProviders = {
      ...mockOffer,
      providers: [
        { name: 'Provider A', price: 5000, deep_link: 'https://a.com', rating: 85 },
        { name: 'Provider B', price: 4800, deep_link: 'https://b.com', rating: 82 },
      ],
    }
    
    render(<ResultCard offer={offerWithMultipleProviders} onProviderSelect={mockOnProviderSelect} />)
    
    const showAllButton = screen.getByTestId('show-all-providers')
    fireEvent.click(showAllButton)
    
    expect(screen.getByTestId('provider-card-Provider B')).toBeInTheDocument()
  })
})
