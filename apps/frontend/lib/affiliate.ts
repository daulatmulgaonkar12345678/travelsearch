/**
 * Affiliate Link Builder
 * 
 * Builds affiliate URLs directly on the frontend for immediate redirects.
 * No backend dependency - ensures fast, reliable redirects to partner sites.
 */

/**
 * Aviasales/Travelpayouts Configuration
 * Hardcoded for reliability - no env vars needed on frontend
 */
const AVIASALES_CONFIG = {
  baseUrl: 'https://aviasales.tpx.lt/eqOxwsZu',
  marker: '689331',
}

export interface FlightSearchParams {
  origin: string
  destination: string
  departDate: string
  returnDate?: string
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
 * Build Aviasales flight affiliate URL
 * Returns a direct link to Aviasales with our affiliate marker
 */
export function buildAviasalesFlightUrl(params: FlightSearchParams): string {
  const {
    origin,
    destination,
    departDate,
    returnDate,
    adults = 1,
    children = 0,
    infants = 0,
  } = params

  // Travelpayouts URL structure
  let url = `${AVIASALES_CONFIG.baseUrl}?`
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

  // Add affiliate marker for commission tracking
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
