/**
 * Unified Recent Search Store
 * 
 * Manages automatic storage of recent searches across ALL transport modes:
 * - Flights
 * - Trains
 * - Buses
 * - Hotels
 * 
 * All searches appear together in one unified list.
 * 
 * IMPORTANT: This store saves SEARCH PARAMETERS only.
 * Prices shown are for reference/display only - NOT final prices.
 * When user re-runs a search, the system ALWAYS fetches live data.
 * 
 * Features:
 * - Automatically stores every successful search
 * - No login required, no explicit save action needed
 * - Keeps last 12 searches (FIFO)
 * - Deduplicates identical searches
 * - Expires searches after 7 days
 * 
 * localStorage key: travelsearch_recent_searches
 */

export type TransportMode = 'flight' | 'train' | 'bus' | 'hotel'

export interface RecentSearch {
  // Core identifier
  mode: TransportMode
  
  // Search parameters (ALWAYS used for re-search)
  origin: string
  destination: string
  departureDate: string
  returnDate?: string
  passengers: number
  timestamp: string // ISO string - when search was performed
  
  // Mode-specific fields
  cabinClass?: string      // Flights
  tripType?: string        // Flights: 'oneway' | 'roundtrip'
  trainClass?: string      // Trains: 'SL' | '3A' | '2A' | '1A' | 'CC'
  busType?: string         // Buses: 'all' | 'non_ac' | 'ac_seater' | 'ac_sleeper'
  
  // Display-only fields (NOT used as final prices)
  displayPrice?: number
  displayCurrency?: string
}

const STORAGE_KEY = 'travelsearch_recent_searches'
const LEGACY_KEY = 'travelsearch_recent_flights' // For migration
const MAX_SEARCHES = 12
const EXPIRY_DAYS = 7

/**
 * Check if a search entry has expired (older than 7 days)
 */
function isExpired(search: RecentSearch): boolean {
  const searchTime = new Date(search.timestamp).getTime()
  const now = Date.now()
  const expiryMs = EXPIRY_DAYS * 24 * 60 * 60 * 1000
  return now - searchTime > expiryMs
}

/**
 * Check if two searches are identical (for deduplication)
 * Only compares search PARAMETERS, not prices
 */
function areSearchesEqual(a: RecentSearch, b: RecentSearch): boolean {
  return (
    a.mode === b.mode &&
    a.origin === b.origin &&
    a.destination === b.destination &&
    a.departureDate === b.departureDate &&
    a.returnDate === b.returnDate &&
    a.passengers === b.passengers
  )
}

/**
 * Migrate legacy flight-only searches to new unified format
 */
function migrateLegacySearches(): RecentSearch[] {
  if (typeof window === 'undefined') return []
  
  try {
    const legacyData = localStorage.getItem(LEGACY_KEY)
    if (!legacyData) return []
    
    const legacySearches = JSON.parse(legacyData)
    
    // Convert legacy format to new unified format
    const migrated: RecentSearch[] = legacySearches.map((s: any) => ({
      mode: 'flight' as TransportMode,
      origin: s.origin,
      destination: s.destination,
      departureDate: s.departureDate,
      returnDate: s.returnDate,
      passengers: s.adults || 1,
      timestamp: s.timestamp,
      cabinClass: s.cabinClass,
      tripType: s.tripType,
      displayPrice: s.displayPrice,
      displayCurrency: s.displayCurrency,
    }))
    
    // Save to new key and remove legacy
    localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated))
    localStorage.removeItem(LEGACY_KEY)
    
    return migrated
  } catch (e) {
    console.warn('[RecentSearchStore] Migration failed:', e)
    return []
  }
}

/**
 * Get all recent searches from localStorage
 * Automatically filters out expired searches and migrates legacy data
 */
export function getRecentSearches(): RecentSearch[] {
  if (typeof window === 'undefined') return []
  
  try {
    // Check for legacy data and migrate
    const legacyExists = localStorage.getItem(LEGACY_KEY)
    if (legacyExists) {
      return migrateLegacySearches()
    }
    
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return []
    
    const searches: RecentSearch[] = JSON.parse(stored)
    
    // Filter out expired searches
    const validSearches = searches.filter(s => !isExpired(s))
    
    // If we filtered out any expired searches, save the cleaned list
    if (validSearches.length !== searches.length) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(validSearches))
    }
    
    return validSearches
  } catch (e) {
    console.warn('[RecentSearchStore] Failed to load searches:', e)
    return []
  }
}

/**
 * Get recent searches filtered by mode
 */
export function getRecentSearchesByMode(mode: TransportMode): RecentSearch[] {
  return getRecentSearches().filter(s => s.mode === mode)
}

/**
 * Add a new search to recent searches
 * Called automatically after a successful search
 * 
 * @param search - The search parameters to save
 * @returns The updated list of recent searches
 */
export function addRecentSearch(search: Omit<RecentSearch, 'timestamp'>): RecentSearch[] {
  if (typeof window === 'undefined') return []
  
  try {
    const existing = getRecentSearches()
    
    // Create new search entry with timestamp
    const newSearch: RecentSearch = {
      ...search,
      timestamp: new Date().toISOString()
    }
    
    // Check for duplicate - if exists, update timestamp and move to front
    const duplicateIndex = existing.findIndex(s => areSearchesEqual(s, newSearch))
    
    let updated: RecentSearch[]
    
    if (duplicateIndex !== -1) {
      // Remove duplicate and add updated version at front
      existing.splice(duplicateIndex, 1)
      updated = [newSearch, ...existing]
    } else {
      // Add new search at front
      updated = [newSearch, ...existing]
    }
    
    // Keep only last MAX_SEARCHES
    updated = updated.slice(0, MAX_SEARCHES)
    
    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    
    return updated
  } catch (e) {
    console.warn('[RecentSearchStore] Failed to save search:', e)
    return getRecentSearches()
  }
}

/**
 * Update the display price for a recent search
 * This is for UI display only - NOT the final price
 */
export function updateRecentSearchPrice(
  mode: TransportMode,
  origin: string,
  destination: string,
  departureDate: string,
  price: number,
  currency: string
): void {
  if (typeof window === 'undefined') return
  
  try {
    const searches = getRecentSearches()
    const index = searches.findIndex(s => 
      s.mode === mode &&
      s.origin === origin &&
      s.destination === destination &&
      s.departureDate === departureDate
    )
    
    if (index !== -1) {
      searches[index].displayPrice = price
      searches[index].displayCurrency = currency
      localStorage.setItem(STORAGE_KEY, JSON.stringify(searches))
    }
  } catch (e) {
    console.warn('[RecentSearchStore] Failed to update price:', e)
  }
}

/**
 * Remove a specific search from recent searches
 */
export function removeRecentSearch(search: RecentSearch): RecentSearch[] {
  if (typeof window === 'undefined') return []
  
  try {
    const existing = getRecentSearches()
    const updated = existing.filter(s => !areSearchesEqual(s, search))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    return updated
  } catch (e) {
    console.warn('[RecentSearchStore] Failed to remove search:', e)
    return getRecentSearches()
  }
}

/**
 * Clear all recent searches
 */
export function clearRecentSearches(): void {
  if (typeof window === 'undefined') return
  
  try {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(LEGACY_KEY) // Also clear legacy
  } catch (e) {
    console.warn('[RecentSearchStore] Failed to clear searches:', e)
  }
}

/**
 * Format a date string for display (YYYY-MM-DD → "Jan 15")
 */
export function formatSearchDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr + 'T00:00:00')
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

/**
 * Format relative time ("2 hours ago", "Yesterday", etc.)
 */
export function formatRelativeTime(timestamp: string): string {
  const now = Date.now()
  const searchTime = new Date(timestamp).getTime()
  const diffMs = now - searchTime
  
  const minutes = Math.floor(diffMs / (1000 * 60))
  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return formatSearchDate(timestamp.split('T')[0])
}

/**
 * Build search URL from recent search params
 * Used when user clicks to re-run a search
 */
export function buildSearchUrl(search: RecentSearch): string {
  const params = new URLSearchParams()
  
  // Common params
  params.set('origin', search.origin)
  params.set('destination', search.destination)
  params.set('departure_date', search.departureDate)
  params.set('passengers', String(search.passengers || 1))
  
  // Mode-specific params
  if (search.mode === 'flight') {
    params.set('trip_type', search.tripType || 'oneway')
    params.set('adults', String(search.passengers || 1))
    params.set('cabin_class', search.cabinClass || 'economy')
    if (search.returnDate && search.tripType === 'roundtrip') {
      params.set('return_date', search.returnDate)
    }
    return `/flights/results?${params.toString()}`
  }
  
  if (search.mode === 'train') {
    if (search.trainClass) {
      params.set('train_class', search.trainClass)
    }
    return `/trains/results?${params.toString()}`
  }
  
  if (search.mode === 'bus') {
    if (search.busType) {
      params.set('bus_type', search.busType)
    }
    return `/buses/results?${params.toString()}`
  }
  
  if (search.mode === 'hotel') {
    params.set('city', search.destination)
    params.set('check_in', search.departureDate)
    if (search.returnDate) {
      params.set('check_out', search.returnDate)
    }
    return `/hotels/results?${params.toString()}`
  }
  
  return '/'
}

/**
 * Get mode display name
 */
export function getModeDisplayName(mode: TransportMode): string {
  const names: Record<TransportMode, string> = {
    flight: 'Flight',
    train: 'Train',
    bus: 'Bus',
    hotel: 'Hotel',
  }
  return names[mode] || mode
}
