/**
 * Recent Search Store
 * 
 * Manages automatic storage of recent flight searches in localStorage.
 * 
 * IMPORTANT: This store saves SEARCH PARAMETERS only.
 * Prices shown are for reference/display only - NOT final prices.
 * When user re-runs a search, the system ALWAYS fetches live prices.
 * 
 * Features:
 * - Automatically stores every successful flight search
 * - No login required, no explicit save action needed
 * - Keeps last 8 searches (FIFO)
 * - Deduplicates identical searches
 * - Expires searches after 7 days
 * 
 * localStorage key: travelsearch_recent_flights
 */

export interface RecentSearch {
  // Search parameters (ALWAYS used for re-search)
  origin: string
  destination: string
  departureDate: string
  returnDate?: string
  adults: number
  cabinClass: string
  tripType: string
  timestamp: string // ISO string - when search was performed
  
  // Display-only fields (NOT used as final prices)
  // These are just for showing approximate prices in the UI
  // Real prices are ALWAYS fetched fresh when user clicks
  displayPrice?: number      // Renamed from lastKnownPrice for clarity
  displayCurrency?: string   // Renamed from lastKnownCurrency for clarity
}

const STORAGE_KEY = 'travelsearch_recent_flights'
const MAX_SEARCHES = 8
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
    a.origin === b.origin &&
    a.destination === b.destination &&
    a.departureDate === b.departureDate &&
    a.returnDate === b.returnDate &&
    a.adults === b.adults &&
    a.cabinClass === b.cabinClass
  )
}

/**
 * Get all recent searches from localStorage
 * Automatically filters out expired searches
 */
export function getRecentSearches(): RecentSearch[] {
  if (typeof window === 'undefined') return []
  
  try {
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
 * Add a new search to recent searches
 * Called automatically after a successful flight search
 * 
 * NOTE: displayPrice is for UI reference only.
 * When user re-runs this search, prices are ALWAYS fetched fresh.
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
  const params = new URLSearchParams({
    origin: search.origin,
    destination: search.destination,
    departure_date: search.departureDate,
    trip_type: search.tripType || 'oneway',
    adults: String(search.adults || 1),
    cabin_class: search.cabinClass || 'economy',
  })
  
  if (search.returnDate && search.tripType === 'roundtrip') {
    params.set('return_date', search.returnDate)
  }
  
  return `/flights/results?${params.toString()}`
}
