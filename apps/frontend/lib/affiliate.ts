/**
 * Affiliate Link Builder
 * 
 * Builds affiliate URLs directly on the frontend for immediate redirects.
 * Uses Aviasales path-based deep links for direct search results.
 * No backend dependency - ensures fast, reliable redirects to partner sites.
 */

/**
 * Aviasales/Travelpayouts Configuration
 */
const AVIASALES_CONFIG = {
  // Direct domain for path-based deep links (more reliable)
  directUrl: 'https://www.aviasales.com',
  // Affiliate tracking URL
  trackingUrl: 'https://aviasales.tpx.lt/eqOxwsZu',
  marker: '689331',
}

export interface FlightSearchParams {
  origin: string
  destination: string
  departDate: string  // YYYY-MM-DD format
  returnDate?: string // YYYY-MM-DD format
  adults?: number
  children?: number
  infants?: number
}

export interface HotelSearchParams {
  city: string
  checkIn: string
  checkOut: string
  adults?: number
}

/**
 * Format date from YYYY-MM-DD to DDMM for Aviasales path
 * Example: "2025-01-15" → "1501"
 */
function formatDateForAviasales(dateStr: string): string {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length !== 3) return ''
  const day = parts[2]
  const month = parts[1]
  return `${day}${month}`
}

/**
 * Build Aviasales path-based deep link
 * 
 * Format: /search/{ORIGIN}{DDMM}{DEST}{passengers}
 * - One-way:    /search/BOM1501DEL1     (BOM → DEL, 15 Jan, 1 adult)
 * - Round-trip: /search/BOM1501DEL20011 (BOM → DEL, 15 Jan, return 20 Jan, 1 adult)
 * 
 * Passengers format: {adults}{children}{infants} (only if non-default)
 */
function buildAviasalesSearchPath(params: FlightSearchParams): string {
  const {
    origin,
    destination,
    departDate,
    returnDate,
    adults = 1,
    children = 0,
    infants = 0,
  } = params

  const departDDMM = formatDateForAviasales(departDate)
  if (!departDDMM) {
    console.warn('Invalid depart date for Aviasales URL:', departDate)
    return ''
  }

  // Build path: ORIGIN + DDMM + DEST + (return DDMM if round-trip) + passengers
  let path = `${origin}${departDDMM}${destination}`
  
  if (returnDate) {
    const returnDDMM = formatDateForAviasales(returnDate)
    if (returnDDMM) {
      path += returnDDMM
    }
  }
  
  // Add passenger count (simplified: just total adults for now)
  // Full format would be: adults + children ages + infants
  path += adults.toString()
  
  return `/search/${path}`
}

/**
 * Build Aviasales flight affiliate URL
 * Returns a direct deep link to Aviasales SEARCH RESULTS (not homepage)
 * 
 * Uses path-based deep links for reliable direct-to-results navigation:
 * - One-way:    aviasales.com/search/BOM1501DEL1
 * - Round-trip: aviasales.com/search/BOM1501DEL20011
 */
export function buildAviasalesFlightUrl(params: FlightSearchParams): string {
  const searchPath = buildAviasalesSearchPath(params)
  
  if (!searchPath) {
    // Fallback to query-param based URL if path building fails
    return buildAviasalesFlightUrlFallback(params)
  }
  
  // Build final URL with affiliate marker
  const url = new URL(searchPath, AVIASALES_CONFIG.directUrl)
  url.searchParams.set('marker', AVIASALES_CONFIG.marker)
  
  return url.toString()
}

/**
 * Fallback URL builder using query parameters
 * Used if path-based URL building fails
 */
function buildAviasalesFlightUrlFallback(params: FlightSearchParams): string {
  const {
    origin,
    destination,
    departDate,
    returnDate,
    adults = 1,
    children = 0,
    infants = 0,
  } = params

  let url = `${AVIASALES_CONFIG.trackingUrl}?`
  url += `origin_iata=${encodeURIComponent(origin)}`
  url += `&destination_iata=${encodeURIComponent(destination)}`
  url += `&depart_date=${encodeURIComponent(departDate)}`

  if (returnDate) {
    url += `&return_date=${encodeURIComponent(returnDate)}`
  }

  if (adults > 1) {
    url += `&adults=${adults}`
  }

  if (children > 0) {
    url += `&children=${children}`
  }

  if (infants > 0) {
    url += `&infants=${infants}`
  }

  url += `&marker=${AVIASALES_CONFIG.marker}`

  return url
}

/**
 * Build Aviasales hotel affiliate URL
 * Returns a direct link to Aviasales Hotels with our affiliate marker
 */
export function buildAviasalesHotelUrl(params: HotelSearchParams): string {
  const { city, checkIn, checkOut, adults = 2 } = params

  // Aviasales hotel URL structure (adjust based on actual Travelpayouts docs)
  let url = `${AVIASALES_CONFIG.baseUrl}?`
  url += `city=${encodeURIComponent(city)}`
  url += `&checkIn=${encodeURIComponent(checkIn)}`
  url += `&checkOut=${encodeURIComponent(checkOut)}`

  if (adults > 2) {
    url += `&adults=${adults}`
  }

  // Add affiliate marker
  url += `&marker=${AVIASALES_CONFIG.marker}`

  return url
}

/**
 * Log affiliate click (fire-and-forget)
 * This is optional and should never block the redirect
 */
export async function logAffiliateClick(
  provider: string,
  route: string,
  offerId: string,
  price?: number
): Promise<void> {
  try {
    // Fire-and-forget - don't await the response
    fetch('/api/clicks/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider,
        route,
        offer_id: offerId,
        price: price || 0,
        timestamp: new Date().toISOString(),
      }),
      // Don't wait for response
      keepalive: true,
    }).catch((err) => {
      // Silently fail - logging should never break redirect
      console.warn('Click logging failed (non-blocking):', err)
    })
  } catch (err) {
    // Silently fail - logging should never break redirect
    console.warn('Click logging error (non-blocking):', err)
  }
}
