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
 * This approach ensures search data persists across navigation,
 * even if URL params get truncated or modified.
 */

export type ServiceType = 'flights' | 'hotels' | 'buses' | 'trains'

export interface FlightSearchPayload {
  service: 'flights'
  origin: string           // IATA code (DEL)
  destination: string      // IATA code (BOM)
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
  city: string
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
    console.log(`[ModifySearch] Saved ${payload.service} payload to localStorage`)
  } catch (e) {
    console.warn('[ModifySearch] Failed to save payload:', e)
  }
}

/**
 * Get saved search payload for a service
 * Called when homepage loads with ?modify=true
 */
export function getModifySearchPayload<T extends SearchPayload>(service: ServiceType): T | null {
  if (typeof window === 'undefined') return null
  
  try {
    const key = getStorageKey(service)
    const stored = localStorage.getItem(key)
    if (!stored) return null
    
    const data = JSON.parse(stored) as T & { timestamp: string }
    
    // Check if payload is stale (older than 1 hour)
    const timestamp = new Date(data.timestamp).getTime()
    const now = Date.now()
    const oneHour = 60 * 60 * 1000
    
    if (now - timestamp > oneHour) {
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
 * Called after successful form hydration or when payload is stale
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
