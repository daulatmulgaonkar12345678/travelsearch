/**
 * Modify Search Store
 * 
 * Stores the last search payload per service type for "Modify Search" functionality.
 * This is the SINGLE SOURCE OF TRUTH for hydrating the search form when user clicks "Modify".
 * 
 * Flow:
 * 1. User clicks "Modify Search" on results/vendor page
 * 2. ModifySearchButton saves current search params to localStorage
 * 3. Homepage loads with ?modify=true
 * 4. SearchBarV3 reads from localStorage and hydrates form state
 * 
 * IMPORTANT: Store full objects (not just codes) to pass validation on hydration.
 */

export type ServiceType = 'flights' | 'hotels' | 'buses' | 'trains'

// Full airport object for validation
export interface AirportData {
  iata: string
  name: string
  city: string
  country: string
}

// Hotel destination types
export type HotelDestinationType = 'city' | 'area' | 'hotel'

export interface HotelDestination {
  type: HotelDestinationType
  id: string           // Unique identifier
  label: string        // Display label
  city: string         // Parent city (for all types)
  country: string
  // Type-specific fields
  areaName?: string    // For type='area'
  hotelName?: string   // For type='hotel'
  latitude?: number
  longitude?: number
}

export interface FlightSearchPayload {
  service: 'flights'
  // Store full airport objects for validation
  origin: AirportData
  destination: AirportData
  departure_date: string   // YYYY-MM-DD
  return_date?: string     // YYYY-MM-DD (for roundtrip)
  adults: number
  children?: number
  infants?: number
  cabin_class?: string
  trip_type?: string
}

export interface HotelSearchPayload {
  service: 'hotels'
  // Store full destination object
  destination: HotelDestination
  check_in: string        // YYYY-MM-DD
  check_out: string       // YYYY-MM-DD
  adults: number
  rooms?: number
}

export interface BusSearchPayload {
  service: 'buses'
  origin: string          // City name
  destination: string     // City name
  departure_date: string  // YYYY-MM-DD
  passengers?: number
  bus_type?: string
}

export interface TrainSearchPayload {
  service: 'trains'
  origin: string          // Station code or city name
  destination: string     // Station code or city name
  origin_city?: string    // City name for display
  destination_city?: string
  departure_date: string  // YYYY-MM-DD
  passengers?: number
  train_class?: string
}

export type SearchPayload = 
  | FlightSearchPayload 
  | HotelSearchPayload 
  | BusSearchPayload 
  | TrainSearchPayload

const STORAGE_KEY_PREFIX = 'travelsearch_modify_'

/**
 * Get the storage key for a service
 */
function getStorageKey(service: ServiceType): string {
  return `${STORAGE_KEY_PREFIX}${service}`
}

/**
 * Save search payload for "Modify Search" functionality
 * Called when user clicks "Modify" button
 */
export function saveModifySearchPayload(payload: SearchPayload): void {
  if (typeof window === 'undefined') return
  
  try {
    const key = getStorageKey(payload.service)
    const data = {
      ...payload,
      timestamp: new Date().toISOString()
    }
    localStorage.setItem(key, JSON.stringify(data))
    console.log(`[ModifySearch] Saved ${payload.service} payload to localStorage`, payload)
  } catch (e) {
    console.warn('[ModifySearch] Failed to save payload:', e)
  }
}

/**
 * Get saved search payload for a service
 * Called when homepage loads with ?modify=true
 * NOTE: Does NOT clear payload - caller should clear after successful SUBMIT
 */
export function getModifySearchPayload<T extends SearchPayload>(service: ServiceType): T | null {
  if (typeof window === 'undefined') return null
  
  try {
    const key = getStorageKey(service)
    const stored = localStorage.getItem(key)
    if (!stored) return null
    
    const data = JSON.parse(stored) as T & { timestamp: string }
    
    // Check if payload is stale (older than 2 hours - extended for better UX)
    const timestamp = new Date(data.timestamp).getTime()
    const now = Date.now()
    const twoHours = 2 * 60 * 60 * 1000
    
    if (now - timestamp > twoHours) {
      console.log(`[ModifySearch] Payload for ${service} is stale, clearing`)
      clearModifySearchPayload(service)
      return null
    }
    
    console.log(`[ModifySearch] Retrieved ${service} payload from localStorage`)
    return data
  } catch (e) {
    console.warn('[ModifySearch] Failed to get payload:', e)
    return null
  }
}

/**
 * Clear the saved search payload for a service
 * Should be called AFTER successful search submit, not immediately on hydration
 */
export function clearModifySearchPayload(service: ServiceType): void {
  if (typeof window === 'undefined') return
  
  try {
    const key = getStorageKey(service)
    localStorage.removeItem(key)
    console.log(`[ModifySearch] Cleared ${service} payload`)
  } catch (e) {
    console.warn('[ModifySearch] Failed to clear payload:', e)
  }
}

/**
 * Clear all modify search payloads
 */
export function clearAllModifySearchPayloads(): void {
  if (typeof window === 'undefined') return
  
  const services: ServiceType[] = ['flights', 'hotels', 'buses', 'trains']
  services.forEach(service => clearModifySearchPayload(service))
}

/**
 * AIRPORT LOOKUP - Maps IATA codes to full airport objects
 * Used when we only have codes but need full objects for validation
 * 
 * This is populated from API results or known airports
 */
const KNOWN_AIRPORTS: Record<string, AirportData> = {
  // Major Indian Airports
  'DEL': { iata: 'DEL', name: 'Indira Gandhi International Airport', city: 'Delhi', country: 'India' },
  'BOM': { iata: 'BOM', name: 'Chhatrapati Shivaji Maharaj International Airport', city: 'Mumbai', country: 'India' },
  'BLR': { iata: 'BLR', name: 'Kempegowda International Airport', city: 'Bangalore', country: 'India' },
  'MAA': { iata: 'MAA', name: 'Chennai International Airport', city: 'Chennai', country: 'India' },
  'CCU': { iata: 'CCU', name: 'Netaji Subhas Chandra Bose International Airport', city: 'Kolkata', country: 'India' },
  'HYD': { iata: 'HYD', name: 'Rajiv Gandhi International Airport', city: 'Hyderabad', country: 'India' },
  'PNQ': { iata: 'PNQ', name: 'Pune Airport', city: 'Pune', country: 'India' },
  'GOI': { iata: 'GOI', name: 'Goa International Airport', city: 'Goa', country: 'India' },
  'COK': { iata: 'COK', name: 'Cochin International Airport', city: 'Kochi', country: 'India' },
  'AMD': { iata: 'AMD', name: 'Sardar Vallabhbhai Patel International Airport', city: 'Ahmedabad', country: 'India' },
  'JAI': { iata: 'JAI', name: 'Jaipur International Airport', city: 'Jaipur', country: 'India' },
  'LKO': { iata: 'LKO', name: 'Chaudhary Charan Singh International Airport', city: 'Lucknow', country: 'India' },
  'GAU': { iata: 'GAU', name: 'Lokpriya Gopinath Bordoloi International Airport', city: 'Guwahati', country: 'India' },
  'TRV': { iata: 'TRV', name: 'Trivandrum International Airport', city: 'Thiruvananthapuram', country: 'India' },
  'IXC': { iata: 'IXC', name: 'Chandigarh International Airport', city: 'Chandigarh', country: 'India' },
  'NAG': { iata: 'NAG', name: 'Dr. Babasaheb Ambedkar International Airport', city: 'Nagpur', country: 'India' },
  'PAT': { iata: 'PAT', name: 'Jay Prakash Narayan International Airport', city: 'Patna', country: 'India' },
  'IXB': { iata: 'IXB', name: 'Bagdogra Airport', city: 'Bagdogra', country: 'India' },
  'VNS': { iata: 'VNS', name: 'Lal Bahadur Shastri International Airport', city: 'Varanasi', country: 'India' },
  'SXR': { iata: 'SXR', name: 'Sheikh ul-Alam International Airport', city: 'Srinagar', country: 'India' },
  'IDR': { iata: 'IDR', name: 'Devi Ahilyabai Holkar Airport', city: 'Indore', country: 'India' },
  'BBI': { iata: 'BBI', name: 'Biju Patnaik International Airport', city: 'Bhubaneswar', country: 'India' },
  'IXR': { iata: 'IXR', name: 'Birsa Munda Airport', city: 'Ranchi', country: 'India' },
  'RPR': { iata: 'RPR', name: 'Swami Vivekananda Airport', city: 'Raipur', country: 'India' },
  'VTZ': { iata: 'VTZ', name: 'Visakhapatnam Airport', city: 'Visakhapatnam', country: 'India' },
  'IXE': { iata: 'IXE', name: 'Mangalore International Airport', city: 'Mangalore', country: 'India' },
  'CJB': { iata: 'CJB', name: 'Coimbatore International Airport', city: 'Coimbatore', country: 'India' },
  'TRZ': { iata: 'TRZ', name: 'Tiruchirappalli International Airport', city: 'Tiruchirappalli', country: 'India' },
  'IXM': { iata: 'IXM', name: 'Madurai Airport', city: 'Madurai', country: 'India' },
  'UDR': { iata: 'UDR', name: 'Maharana Pratap Airport', city: 'Udaipur', country: 'India' },
  'BDQ': { iata: 'BDQ', name: 'Vadodara Airport', city: 'Vadodara', country: 'India' },
  'RAJ': { iata: 'RAJ', name: 'Rajkot Airport', city: 'Rajkot', country: 'India' },
  'STV': { iata: 'STV', name: 'Surat Airport', city: 'Surat', country: 'India' },
  // International Airports
  'DXB': { iata: 'DXB', name: 'Dubai International Airport', city: 'Dubai', country: 'UAE' },
  'SIN': { iata: 'SIN', name: 'Singapore Changi Airport', city: 'Singapore', country: 'Singapore' },
  'BKK': { iata: 'BKK', name: 'Suvarnabhumi Airport', city: 'Bangkok', country: 'Thailand' },
  'LHR': { iata: 'LHR', name: 'Heathrow Airport', city: 'London', country: 'United Kingdom' },
  'JFK': { iata: 'JFK', name: 'John F. Kennedy International Airport', city: 'New York', country: 'USA' },
  'LAX': { iata: 'LAX', name: 'Los Angeles International Airport', city: 'Los Angeles', country: 'USA' },
  'SFO': { iata: 'SFO', name: 'San Francisco International Airport', city: 'San Francisco', country: 'USA' },
  'HKG': { iata: 'HKG', name: 'Hong Kong International Airport', city: 'Hong Kong', country: 'Hong Kong' },
  'KUL': { iata: 'KUL', name: 'Kuala Lumpur International Airport', city: 'Kuala Lumpur', country: 'Malaysia' },
  'DOH': { iata: 'DOH', name: 'Hamad International Airport', city: 'Doha', country: 'Qatar' },
  'AUH': { iata: 'AUH', name: 'Abu Dhabi International Airport', city: 'Abu Dhabi', country: 'UAE' },
  'FRA': { iata: 'FRA', name: 'Frankfurt Airport', city: 'Frankfurt', country: 'Germany' },
  'CDG': { iata: 'CDG', name: 'Charles de Gaulle Airport', city: 'Paris', country: 'France' },
  'AMS': { iata: 'AMS', name: 'Amsterdam Schiphol Airport', city: 'Amsterdam', country: 'Netherlands' },
  'IST': { iata: 'IST', name: 'Istanbul Airport', city: 'Istanbul', country: 'Turkey' },
  'MLE': { iata: 'MLE', name: 'Velana International Airport', city: 'Male', country: 'Maldives' },
  'CMB': { iata: 'CMB', name: 'Bandaranaike International Airport', city: 'Colombo', country: 'Sri Lanka' },
  'DAC': { iata: 'DAC', name: 'Hazrat Shahjalal International Airport', city: 'Dhaka', country: 'Bangladesh' },
  'KTM': { iata: 'KTM', name: 'Tribhuvan International Airport', city: 'Kathmandu', country: 'Nepal' },
}

/**
 * Get full airport data from IATA code
 * Returns a valid Airport object or creates one with minimal data
 */
export function getAirportByCode(iata: string): AirportData | null {
  const code = iata.toUpperCase()
  
  // Check known airports first
  if (KNOWN_AIRPORTS[code]) {
    return KNOWN_AIRPORTS[code]
  }
  
  // Return null if not found - caller should handle
  return null
}

/**
 * Create a minimal valid airport object from code
 * Use when airport isn't in lookup but we still need a valid object
 */
export function createAirportFromCode(iata: string): AirportData {
  const code = iata.toUpperCase()
  
  // Check known airports first
  if (KNOWN_AIRPORTS[code]) {
    return KNOWN_AIRPORTS[code]
  }
  
  // Create minimal valid airport
  return {
    iata: code,
    name: `${code} Airport`,
    city: code,  // Use code as city fallback
    country: 'Unknown'
  }
}
