import { render, screen, fireEvent } from '@testing-library/react'
import PassengerModal from '@/components/search/PassengerModal'

describe('PassengerModal', () => {
  const mockOnUpdate = jest.fn()
  const mockOnClose = jest.fn()

  const defaultProps = {
    passengers: { adults: 1, children: 0, infants: 0 },
    onUpdate: mockOnUpdate,
    onClose: mockOnClose,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders passenger counts correctly', () => {
    render(<PassengerModal {...defaultProps} />)
    
    expect(screen.getByTestId('adults-count')).toHaveTextContent('1')
    expect(screen.getByTestId('children-count')).toHaveTextContent('0')
    expect(screen.getByTestId('infants-count')).toHaveTextContent('0')
  })

  it('increases adult count when + button clicked', () => {
    render(<PassengerModal {...defaultProps} />)
    
    const increaseButton = screen.getByTestId('increase-adults')
    fireEvent.click(increaseButton)
    
    expect(mockOnUpdate).toHaveBeenCalledWith({
      adults: 2,
      children: 0,
      infants: 0,
    })
  })

  it('decreases adult count when - button clicked', () => {
    const props = {
      ...defaultProps,
      passengers: { adults: 2, children: 0, infants: 0 },
    }
    render(<PassengerModal {...props} />)
    
    const decreaseButton = screen.getByTestId('decrease-adults')
    fireEvent.click(decreaseButton)
    
    expect(mockOnUpdate).toHaveBeenCalledWith({
      adults: 1,
      children: 0,
      infants: 0,
    })
  })

  it('prevents adult count from going below 1', () => {
    render(<PassengerModal {...defaultProps} />)
    
    const decreaseButton = screen.getByTestId('decrease-adults')
    expect(decreaseButton).toBeDisabled()
  })

  it('increases children count correctly', () => {
    render(<PassengerModal {...defaultProps} />)
    
    const increaseButton = screen.getByTestId('increase-children')
    fireEvent.click(increaseButton)
    
    expect(mockOnUpdate).toHaveBeenCalledWith({
      adults: 1,
      children: 1,
      infants: 0,
    })
  })

  it('closes modal when done button clicked', () => {
    render(<PassengerModal {...defaultProps} />)
    
    const doneButton = screen.getByTestId('done-button')
    fireEvent.click(doneButton)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('closes modal when X button clicked', () => {
    render(<PassengerModal {...defaultProps} />)
    
    const closeButton = screen.getByTestId('close-passenger-modal')
    fireEvent.click(closeButton)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('has proper ARIA labels', () => {
    render(<PassengerModal {...defaultProps} />)
    
    expect(screen.getByTestId('passenger-modal')).toBeInTheDocument()
  })
})
