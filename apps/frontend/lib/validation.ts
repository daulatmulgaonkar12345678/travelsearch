/**
 * Centralized validation utilities for TravelSearch
 * Ensures consistent validation across all components
 */

export interface ValidationResult {
  isValid: boolean
  error?: string
}

export class FlightValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'FlightValidationError'
  }
}

export class HotelValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'HotelValidationError'
  }
}

/**
 * Flight validation utilities
 */
export const FlightValidator = {
  /**
   * Validate origin and destination are different
   */
  validateOriginDestination(origin: string, destination: string): ValidationResult {
    if (!origin || !destination) {
      return { isValid: false, error: 'Please select both origin and destination' }
    }
    
    if (origin.toUpperCase() === destination.toUpperCase()) {
      return { isValid: false, error: 'Origin and destination must be different' }
    }
    
    return { isValid: true }
  },

  /**
   * Validate departure date is at least tomorrow
   */
  validateDepartureDate(departureDate: string): ValidationResult {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const departure = new Date(departureDate)
    
    if (departure <= today) {
      return { isValid: false, error: 'Departure must be at least tomorrow' }
    }
    
    return { isValid: true }
  },

  /**
   * Validate return date is after departure
   */
  validateReturnDate(departureDate: string, returnDate: string): ValidationResult {
    const departure = new Date(departureDate)
    const returnD = new Date(returnDate)
    
    if (returnD <= departure) {
      return { isValid: false, error: 'Return date must be after departure date' }
    }
    
    return { isValid: true }
  },

  /**
   * Validate multicity segments don't overlap
   */
  validateMulticitySegments(segments: Array<{ origin: string; destination: string; date: string }>): ValidationResult {
    if (segments.length < 2) {
      return { isValid: false, error: 'Multi-city requires at least 2 flights' }
    }

    // Check all segments have data
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i]
      if (!seg.origin || !seg.destination || !seg.date) {
        return { isValid: false, error: `Flight ${i + 1}: Please fill all fields` }
      }

      // Check origin !== destination for each segment
      if (seg.origin.toUpperCase() === seg.destination.toUpperCase()) {
        return { isValid: false, error: `Flight ${i + 1}: Origin and destination must be different` }
      }
    }

    // Check dates are in order
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    for (let i = 0; i < segments.length; i++) {
      const currentDate = new Date(segments[i].date)
      
      // First segment must be at least tomorrow
      if (i === 0 && currentDate <= today) {
        return { isValid: false, error: 'First flight must be at least tomorrow' }
      }

      // Each segment must be after previous
      if (i > 0) {
        const prevDate = new Date(segments[i - 1].date)
        if (currentDate <= prevDate) {
          return { isValid: false, error: `Flight ${i + 1} must be after Flight ${i}` }
        }
      }
    }

    return { isValid: true }
  },

  /**
   * Validate passenger configuration
   */
  validatePassengers(adults: number, children: number, infants: number): ValidationResult {
    if (adults < 1) {
      return { isValid: false, error: 'At least 1 adult is required' }
    }

    if (infants > adults) {
      return { isValid: false, error: 'Number of infants cannot exceed number of adults' }
    }

    const total = adults + children + infants
    if (total > 9) {
      return { isValid: false, error: 'Maximum 9 passengers allowed' }
    }

    return { isValid: true }
  }
}

/**
 * Hotel validation utilities
 */
export const HotelValidator = {
  /**
   * Validate check-in date is at least tomorrow
   */
  validateCheckInDate(checkIn: string): ValidationResult {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const checkInDate = new Date(checkIn)
    
    if (checkInDate <= today) {
      return { isValid: false, error: 'Check-in must be at least tomorrow' }
    }
    
    return { isValid: true }
  },

  /**
   * Validate check-out is after check-in (minimum 1 night)
   */
  validateCheckOutDate(checkIn: string, checkOut: string): ValidationResult {
    const checkInDate = new Date(checkIn)
    const checkOutDate = new Date(checkOut)
    
    if (checkOutDate <= checkInDate) {
      return { isValid: false, error: 'Check-out must be at least 1 day after check-in' }
    }

    // Ensure at least 1 night stay
    const nightsDiff = Math.floor((checkOutDate.getTime() - checkInDate.getTime()) / (1000 * 60 * 60 * 24))
    if (nightsDiff < 1) {
      return { isValid: false, error: 'Minimum stay is 1 night' }
    }
    
    return { isValid: true }
  },

  /**
   * Validate room configuration
   */
  validateRoomConfiguration(rooms: Array<{ adults: number; children: number[] }>): ValidationResult {
    if (rooms.length < 1) {
      return { isValid: false, error: 'At least 1 room is required' }
    }

    for (let i = 0; i < rooms.length; i++) {
      const room = rooms[i]
      
      // Each room must have at least 1 adult
      if (room.adults < 1) {
        return { isValid: false, error: `Room ${i + 1}: At least 1 adult required` }
      }

      // Check maximum occupancy per room
      const totalGuests = room.adults + room.children.length
      if (totalGuests > 8) {
        return { isValid: false, error: `Room ${i + 1}: Maximum 8 guests per room` }
      }
    }

    return { isValid: true }
  },

  /**
   * Validate maximum stay duration
   */
  validateStayDuration(checkIn: string, checkOut: string, maxDays: number = 365): ValidationResult {
    const checkInDate = new Date(checkIn)
    const checkOutDate = new Date(checkOut)
    
    const daysDiff = Math.floor((checkOutDate.getTime() - checkInDate.getTime()) / (1000 * 60 * 60 * 24))
    
    if (daysDiff > maxDays) {
      return { isValid: false, error: `Maximum stay is ${maxDays} days` }
    }
    
    return { isValid: true }
  }
}

/**
 * General utilities
 */
export const getTomorrowDate = (): string => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
}

export const getDaysFromNow = (days: number): string => {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().split('T')[0]
}

export const formatDateForDisplay = (isoDate: string): string => {
  const date = new Date(isoDate)
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
