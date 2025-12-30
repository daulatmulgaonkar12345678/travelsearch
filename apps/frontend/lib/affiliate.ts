/**
 * Affiliate Link Builder
 * 
 * CRITICAL: Flights and Hotels use SEPARATE redirect gateways.
 * 
 * ❌ NEVER use: aviasales.com, aviasales.in (causes CORS errors)
 * ✅ Flights: aviasales.tpx.lt/eqOxwsZu
 * ✅ Hotels: hotellook.tpx.lt/eqOxwsZu (SEPARATE gateway for hotels)
 * 
 * If hotel context is missing, fallback to hotel search page (NOT flights).
 */

/**
 * Travelpayouts Configuration
 * 
 * SEPARATE gateways for each product type to prevent cross-redirects.
 */
const TRAVELPAYOUTS_CONFIG = {
  // Flight redirect gateway
  flightGateway: 'https://aviasales.tpx.lt/eqOxwsZu',
  
  // Hotel redirect gateway (SEPARATE from flights)
  hotelGateway: 'https://hotellook.tpx.lt/eqOxwsZu',
  
  // Affiliate marker
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
 * Build flight affiliate URL
 * 
 * Uses aviasales.tpx.lt gateway (flights only).
 * 
 * @param params Flight search parameters
 * @returns Travelpayouts flight redirect URL
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

  // Use FLIGHT gateway (aviasales.tpx.lt)
  const url = new URL(TRAVELPAYOUTS_CONFIG.flightGateway)
  
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
 * 2. If only city → Use Hotellook gateway (NOT Aviasales)
 * 3. NEVER redirect to flights when hotel context is missing
 * 
 * @param params Hotel search parameters
 * @returns Hotel redirect URL (Booking.com or Hotellook)
 */
export function buildAviasalesHotelUrl(params: HotelSearchParams): string {
  const { city, checkIn, checkOut, adults = 2, hotelName, hotelId } = params

  // Validate required hotel parameters
  if (!city || !checkIn || !checkOut) {
    // Fallback to Hotellook search page (NOT flights)
    return `${TRAVELPAYOUTS_CONFIG.hotelGateway}`
  }

  // If hotel name provided, use Booking.com for hotel-specific search
  if (hotelName) {
    const hotelNameEncoded = encodeURIComponent(hotelName)
    const cityEncoded = encodeURIComponent(city)
    
    return `https://www.booking.com/searchresults.html?ss=${hotelNameEncoded}%2C+${cityEncoded}&checkin=${checkIn}&checkout=${checkOut}&group_adults=${adults}&no_rooms=1`
  }

  // City-level search: Use HOTEL gateway (hotellook.tpx.lt)
  // This ensures we stay on hotel search, never redirect to flights
  const url = new URL(TRAVELPAYOUTS_CONFIG.hotelGateway)
  
  // Format dates for Hotellook (YYYY-MM-DD)
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
 * Falls back to Hotellook city search if hotel name not provided.
 * 
 * @param hotelName Hotel name
 * @param city City name
 * @param checkIn Check-in date (YYYY-MM-DD)
 * @param checkOut Check-out date (YYYY-MM-DD)
 * @param adults Number of adults
 * @returns Hotel-specific Booking.com URL or Hotellook fallback
 */
export function buildHotelSpecificUrl(
  hotelName: string,
  city: string,
  checkIn: string,
  checkOut: string,
  adults: number = 2
): string {
  if (!hotelName) {
    // Fallback to Hotellook city search (NOT flights)
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
