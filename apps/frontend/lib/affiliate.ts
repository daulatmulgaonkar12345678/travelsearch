/**
 * Affiliate Link Builder
 * 
 * CRITICAL: All booking redirects MUST use the Travelpayouts redirect gateway.
 * 
 * ❌ NEVER use: aviasales.com/search/* (causes CORS errors from auth.avs.io)
 * ✅ ALWAYS use: aviasales.tpx.lt/eqOxwsZu (handles JWT internally, no CORS)
 * 
 * This module builds affiliate URLs directly on the frontend for immediate redirects.
 * No backend dependency - ensures fast, reliable redirects to partner sites.
 */

/**
 * Travelpayouts Configuration
 * 
 * MANDATORY: Use ONLY the redirect gateway URL for all bookings.
 */
const TRAVELPAYOUTS_CONFIG = {
  // REQUIRED: Travelpayouts redirect gateway (handles auth internally)
  redirectGateway: 'https://aviasales.tpx.lt/eqOxwsZu',
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
  hotelName?: string  // For hotel-specific deep links
  hotelId?: string    // Provider hotel ID if available
}

/**
 * Build Aviasales flight affiliate URL
 * 
 * CRITICAL: Uses ONLY the Travelpayouts redirect gateway.
 * NEVER uses aviasales.com directly (causes CORS errors).
 * 
 * @param params Flight search parameters
 * @returns Travelpayouts redirect URL with all flight parameters
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

  // Build URL with Travelpayouts redirect gateway
  const url = new URL(TRAVELPAYOUTS_CONFIG.redirectGateway)
  
  // Flight parameters
  url.searchParams.set('origin_iata', origin.toUpperCase())
  url.searchParams.set('destination_iata', destination.toUpperCase())
  url.searchParams.set('depart_date', departDate)
  
  if (returnDate) {
    url.searchParams.set('return_date', returnDate)
  }
  
  // Passenger count
  url.searchParams.set('adults', adults.toString())
  
  if (children > 0) {
    url.searchParams.set('children', children.toString())
  }
  
  if (infants > 0) {
    url.searchParams.set('infants', infants.toString())
  }
  
  // Trip class (0 = economy)
  url.searchParams.set('trip_class', '0')

  return url.toString()
}

/**
 * Build hotel affiliate URL
 * 
 * Strategy:
 * 1. If hotelName provided → Use Booking.com with hotel-specific search
 * 2. If only city → Use Travelpayouts city-level hotel search
 * 
 * @param params Hotel search parameters
 * @returns Booking URL (hotel-specific) or Travelpayouts URL (city-level)
 */
export function buildAviasalesHotelUrl(params: HotelSearchParams): string {
  const { city, checkIn, checkOut, adults = 2, hotelName, hotelId } = params

  // If hotel name provided, use Booking.com for hotel-specific search
  if (hotelName) {
    const hotelNameEncoded = encodeURIComponent(hotelName)
    const cityEncoded = encodeURIComponent(city)
    
    return `https://www.booking.com/searchresults.html?ss=${hotelNameEncoded}%2C+${cityEncoded}&checkin=${checkIn}&checkout=${checkOut}&group_adults=${adults}&no_rooms=1`
  }

  // Fallback: City-level search via Travelpayouts
  const url = new URL(TRAVELPAYOUTS_CONFIG.redirectGateway)
  url.searchParams.set('type', 'hotel')
  url.searchParams.set('destination', city)
  url.searchParams.set('checkIn', checkIn)
  url.searchParams.set('checkOut', checkOut)
  url.searchParams.set('adults', adults.toString())

  return url.toString()
}

/**
 * Build hotel-specific affiliate URL
 * 
 * Uses Booking.com with hotel name search for precise hotel targeting.
 * Falls back to city-level search if hotel name not provided.
 * 
 * @param hotelName Hotel name
 * @param city City name
 * @param checkIn Check-in date (YYYY-MM-DD)
 * @param checkOut Check-out date (YYYY-MM-DD)
 * @param adults Number of adults
 * @returns Hotel-specific Booking.com URL
 */
export function buildHotelSpecificUrl(
  hotelName: string,
  city: string,
  checkIn: string,
  checkOut: string,
  adults: number = 2
): string {
  if (!hotelName) {
    // Fallback to city-level
    return buildAviasalesHotelUrl({ city, checkIn, checkOut, adults })
  }

  const hotelNameEncoded = encodeURIComponent(hotelName)
  const cityEncoded = encodeURIComponent(city)
  
  return `https://www.booking.com/searchresults.html?ss=${hotelNameEncoded}%2C+${cityEncoded}&checkin=${checkIn}&checkout=${checkOut}&group_adults=${adults}&no_rooms=1`
}

/**
 * Log affiliate click (fire-and-forget)
 * 
 * This is optional and should NEVER block the redirect.
 * If logging fails, the redirect MUST still proceed.
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
    }).catch(() => {
      // Silently fail - logging should never break redirect
    })
  } catch {
    // Silently fail - logging should never break redirect
  }
}
