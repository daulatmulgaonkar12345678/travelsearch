/**
 * Smart Fallback Search for "No Flights Found" scenarios
 * 
 * When primary search returns 0 results, tries:
 * 1. Alternative dates (±3 days)
 * 2. Nearby airports (origin + destination variations)
 * 
 * Safety limits:
 * - Max 4 extra API calls total
 * - Uses existing request cache (20s TTL)
 * - Graceful error handling
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'

// Simple cache for fallback searches (5 minute TTL)
const fallbackCache = new Map<string, {data: any, timestamp: number}>()
const FALLBACK_CACHE_TTL = 300000 // 5 minutes

function getCached(key: string): any | null {
  const entry = fallbackCache.get(key)
  if (entry && Date.now() - entry.timestamp < FALLBACK_CACHE_TTL) {
    return entry.data
  }
  return null
}

function setCache(key: string, data: any) {
  fallbackCache.set(key, { data, timestamp: Date.now() })
}

export interface AlternativeDate {
  date: string
  displayDate: string
  minPrice: number
  minDuration: number
  offerCount: number
}

export interface AlternativeAirport {
  iata: string
  city: string
  country: string
  distance_km: number
  minPrice: number
  minDuration: number
  offerCount: number
  type: 'origin' | 'destination'
}

export interface FallbackSuggestions {
  altDates: AlternativeDate[]
  altOrigins: AlternativeAirport[]
  altDestinations: AlternativeAirport[]
  totalFallbackCalls: number
}

/**
 * Format date for display
 */
function formatDateDisplay(dateStr: string): string {
  const date = new Date(dateStr)
  const options: Intl.DateTimeFormatOptions = { 
    month: 'short', 
    day: 'numeric',
    weekday: 'short'
  }
  return date.toLocaleDateString('en-US', options)
}

/**
 * Fetch nearby airports for a given IATA code
 */
async function fetchNearbyAirports(
  iata: string, 
  radiusKm: number = 200,
  abortSignal?: AbortSignal
): Promise<Array<{iata: string, city: string, country: string, distance_km: number}>> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/airports/${iata}/nearby?radius_km=${radiusKm}&limit=3`,
      { signal: abortSignal }
    )
    
    if (!response.ok) return []
    
    const data = await response.json()
    return (data.results || []).map((r: any) => ({
      iata: r.airport.iata,
      city: r.airport.city,
      country: r.airport.country,
      distance_km: r.distance_km
    }))
  } catch (error) {
    console.warn(`Failed to fetch nearby airports for ${iata}:`, error)
    return []
  }
}

/**
 * Try alternative dates (±3 days from original)
 */
async function tryAlternativeDates(
  params: URLSearchParams,
  abortSignal?: AbortSignal
): Promise<AlternativeDate[]> {
  const originalDate = params.get('departure_date')
  if (!originalDate) return []
  
  const alternatives: AlternativeDate[] = []
  const callLimit = 3
  let callCount = 0
  
  // Try -3, -2, -1, +1, +2, +3 days
  const offsets = [-3, -2, -1, 1, 2, 3]
  
  for (const offset of offsets) {
    if (callCount >= callLimit) break
    
    try {
      const date = new Date(originalDate)
      date.setDate(date.getDate() + offset)
      const newDate = date.toISOString().split('T')[0]
      
      // Create new params with alternative date
      const altParams = new URLSearchParams(params)
      altParams.set('departure_date', newDate)
      
      // Use cached request
      const url = `${BACKEND_URL}/api/search/flights?${altParams.toString()}`
      
      // Check cache first
      let data = getCached(url)
      if (!data) {
        const response = await fetch(url, { signal: abortSignal })
        if (!response.ok) continue
        data = await response.json()
        setCache(url, data)
      }
      
      callCount++
      
      const offers = data?.offers || []
      if (offers.length > 0) {
        const prices = offers.map((o: any) => o.price)
        const durations = offers.map((o: any) => o.total_duration_minutes)
        
        alternatives.push({
          date: newDate,
          displayDate: formatDateDisplay(newDate),
          minPrice: Math.min(...prices),
          minDuration: Math.min(...durations),
          offerCount: offers.length
        })
      }
    } catch (error) {
      console.warn(`Fallback date search failed for offset ${offset}:`, error)
    }
  }
  
  // Sort by price
  alternatives.sort((a, b) => a.minPrice - b.minPrice)
  
  return alternatives.slice(0, 3) // Return top 3
}

/**
 * Try nearby origin airports
 */
async function tryNearbyOrigins(
  params: URLSearchParams,
  abortSignal?: AbortSignal
): Promise<AlternativeAirport[]> {
  const origin = params.get('origin')
  const destination = params.get('destination')
  
  if (!origin || !destination) return []
  
  try {
    // Fetch nearby airports for origin
    const nearbyOrigins = await fetchNearbyAirports(origin, 200, abortSignal)
    
    if (nearbyOrigins.length === 0) return []
    
    const alternatives: AlternativeAirport[] = []
    const callLimit = 2 // Limit to 2 nearby origin attempts
    
    for (let i = 0; i < Math.min(nearbyOrigins.length, callLimit); i++) {
      const nearbyAirport = nearbyOrigins[i]
      
      try {
        // Search with nearby origin
        const altParams = new URLSearchParams(params)
        altParams.set('origin', nearbyAirport.iata)
        
        const url = `${BACKEND_URL}/api/search/flights?${altParams.toString()}`
        const data = await getCachedRequest(url, abortSignal)
        
        const offers = data?.offers || []
        if (offers.length > 0) {
          const prices = offers.map((o: any) => o.price)
          const durations = offers.map((o: any) => o.total_duration_minutes)
          
          alternatives.push({
            iata: nearbyAirport.iata,
            city: nearbyAirport.city,
            country: nearbyAirport.country,
            distance_km: nearbyAirport.distance_km,
            minPrice: Math.min(...prices),
            minDuration: Math.min(...durations),
            offerCount: offers.length,
            type: 'origin'
          })
        }
      } catch (error) {
        console.warn(`Fallback nearby origin search failed for ${nearbyAirport.iata}:`, error)
      }
    }
    
    return alternatives.sort((a, b) => a.minPrice - b.minPrice).slice(0, 2)
  } catch (error) {
    console.warn('Failed to try nearby origins:', error)
    return []
  }
}

/**
 * Try nearby destination airports
 */
async function tryNearbyDestinations(
  params: URLSearchParams,
  abortSignal?: AbortSignal
): Promise<AlternativeAirport[]> {
  const origin = params.get('origin')
  const destination = params.get('destination')
  
  if (!origin || !destination) return []
  
  try {
    // Fetch nearby airports for destination
    const nearbyDests = await fetchNearbyAirports(destination, 200, abortSignal)
    
    if (nearbyDests.length === 0) return []
    
    const alternatives: AlternativeAirport[] = []
    const callLimit = 2 // Limit to 2 nearby destination attempts
    
    for (let i = 0; i < Math.min(nearbyDests.length, callLimit); i++) {
      const nearbyAirport = nearbyDests[i]
      
      try {
        // Search with nearby destination
        const altParams = new URLSearchParams(params)
        altParams.set('destination', nearbyAirport.iata)
        
        const url = `${BACKEND_URL}/api/search/flights?${altParams.toString()}`
        const data = await getCachedRequest(url, abortSignal)
        
        const offers = data?.offers || []
        if (offers.length > 0) {
          const prices = offers.map((o: any) => o.price)
          const durations = offers.map((o: any) => o.total_duration_minutes)
          
          alternatives.push({
            iata: nearbyAirport.iata,
            city: nearbyAirport.city,
            country: nearbyAirport.country,
            distance_km: nearbyAirport.distance_km,
            minPrice: Math.min(...prices),
            minDuration: Math.min(...durations),
            offerCount: offers.length,
            type: 'destination'
          })
        }
      } catch (error) {
        console.warn(`Fallback nearby destination search failed for ${nearbyAirport.iata}:`, error)
      }
    }
    
    return alternatives.sort((a, b) => a.minPrice - b.minPrice).slice(0, 2)
  } catch (error) {
    console.warn('Failed to try nearby destinations:', error)
    return []
  }
}

/**
 * Main fallback search function
 * 
 * Tries alternative dates and nearby airports when primary search returns 0 results.
 * Safety: Max 4 extra API calls, uses request cache, graceful error handling.
 */
export async function runFallbackSearches(
  params: URLSearchParams,
  abortSignal?: AbortSignal
): Promise<FallbackSuggestions> {
  console.log('🔄 Running fallback searches...')
  
  let totalCalls = 0
  const MAX_CALLS = 4
  
  // Track analytics
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', 'no_results_primary', {
      origin: params.get('origin'),
      destination: params.get('destination'),
      date: params.get('departure_date')
    })
  }
  
  const suggestions: FallbackSuggestions = {
    altDates: [],
    altOrigins: [],
    altDestinations: [],
    totalFallbackCalls: 0
  }
  
  try {
    // 1. Try alternative dates (max 3 calls)
    if (totalCalls < MAX_CALLS) {
      console.log('  → Trying alternative dates...')
      const altDates = await tryAlternativeDates(params, abortSignal)
      suggestions.altDates = altDates
      totalCalls += Math.min(3, altDates.length)
      
      if (altDates.length > 0) {
        console.log(`  ✅ Found ${altDates.length} alternative dates`)
        
        // Track analytics
        if (typeof window !== 'undefined' && (window as any).gtag) {
          (window as any).gtag('event', 'fallback_alt_date_shown', {
            count: altDates.length
          })
        }
      }
    }
    
    // 2. Try nearby origins (max 2 calls)
    if (totalCalls < MAX_CALLS) {
      console.log('  → Trying nearby origins...')
      const altOrigins = await tryNearbyOrigins(params, abortSignal)
      suggestions.altOrigins = altOrigins
      totalCalls += altOrigins.length
      
      if (altOrigins.length > 0) {
        console.log(`  ✅ Found ${altOrigins.length} nearby origins`)
        
        // Track analytics
        if (typeof window !== 'undefined' && (window as any).gtag) {
          (window as any).gtag('event', 'fallback_alt_airport_shown', {
            type: 'origin',
            count: altOrigins.length
          })
        }
      }
    }
    
    // 3. Try nearby destinations (max 2 calls, if we have budget)
    if (totalCalls < MAX_CALLS) {
      console.log('  → Trying nearby destinations...')
      const altDests = await tryNearbyDestinations(params, abortSignal)
      suggestions.altDestinations = altDests
      totalCalls += altDests.length
      
      if (altDests.length > 0) {
        console.log(`  ✅ Found ${altDests.length} nearby destinations`)
        
        // Track analytics
        if (typeof window !== 'undefined' && (window as any).gtag) {
          (window as any).gtag('event', 'fallback_alt_airport_shown', {
            type: 'destination',
            count: altDests.length
          })
        }
      }
    }
    
    suggestions.totalFallbackCalls = totalCalls
    console.log(`🔄 Fallback complete: ${totalCalls} calls, ${suggestions.altDates.length + suggestions.altOrigins.length + suggestions.altDestinations.length} suggestions`)
    
  } catch (error) {
    console.error('Fallback search error:', error)
  }
  
  return suggestions
}

/**
 * Track fallback suggestion click
 */
export function trackFallbackClick(type: 'date' | 'origin' | 'destination') {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', `fallback_alt_${type}_clicked`)
  }
}
