/**
 * Airport Validation Utilities
 * 
 * Provides strict validation for airport inputs
 */

export interface Airport {
  iata: string
  name: string
  city: string
  country: string
  iso_country?: string
}

/**
 * Validates if an airport object is complete and valid
 */
export function isValidAirport(airport: any): airport is Airport {
  if (!airport || typeof airport !== 'object') {
    return false
  }

  return (
    typeof airport.iata === 'string' &&
    airport.iata.length === 3 &&
    /^[A-Z]{3}$/.test(airport.iata) &&
    typeof airport.name === 'string' &&
    airport.name.length > 0 &&
    typeof airport.city === 'string' &&
    airport.city.length > 0 &&
    typeof airport.country === 'string' &&
    airport.country.length > 0
  )
}

/**
 * Validates if origin and destination are different airports
 */
export function areAirportsDifferent(
  origin: Airport | null,
  destination: Airport | null
): boolean {
  if (!origin || !destination) {
    return false
  }

  return origin.iata !== destination.iata
}

/**
 * Validates a complete flight search
 */
export interface FlightSearchValidation {
  isValid: boolean
  errors: string[]
}

export function validateFlightSearch(
  origin: Airport | null,
  destination: Airport | null,
  departureDate: string,
  returnDate?: string,
  tripType: string = 'oneway'
): FlightSearchValidation {
  const errors: string[] = []

  // Validate origin
  if (!origin) {
    errors.push('Please select a departure airport')
  } else if (!isValidAirport(origin)) {
    errors.push('Invalid departure airport selected')
  }

  // Validate destination
  if (!destination) {
    errors.push('Please select an arrival airport')
  } else if (!isValidAirport(destination)) {
    errors.push('Invalid arrival airport selected')
  }

  // Validate airports are different
  if (origin && destination && !areAirportsDifferent(origin, destination)) {
    errors.push('Departure and arrival airports must be different')
  }

  // Validate departure date
  if (!departureDate) {
    errors.push('Please select a departure date')
  } else {
    const depDate = new Date(departureDate)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    if (depDate < today) {
      errors.push('Departure date cannot be in the past')
    }
  }

  // Validate return date for roundtrip
  if (tripType === 'roundtrip') {
    if (!returnDate) {
      errors.push('Please select a return date')
    } else {
      const retDate = new Date(returnDate)
      const depDate = new Date(departureDate)
      
      if (retDate < depDate) {
        errors.push('Return date must be after departure date')
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

/**
 * Extract airport IATA codes from validated airports
 */
export function extractIATACodes(
  origin: Airport | null,
  destination: Airport | null
): { origin: string; destination: string } | null {
  if (!isValidAirport(origin) || !isValidAirport(destination)) {
    return null
  }

  return {
    origin: origin.iata,
    destination: destination.iata,
  }
}
