/**
 * Vendor Deep Link Builder
 * 
 * CRITICAL RULES:
 * 1. Use GLOBAL IDENTIFIERS ONLY:
 *    - Flights: IATA airport codes (DEL, BOM, etc.)
 *    - Trains: IRCTC station codes or city names
 *    - Buses: City names only (no vendor-specific IDs)
 *    - Hotels: Search-based deep links using hotel name + city
 * 
 * 2. NEVER:
 *    - Fetch or store vendor-specific IDs (MMT, Paytm, Agoda IDs)
 *    - Scrape vendor websites
 *    - Rely on internal vendor IDs
 * 
 * 3. DEEP LINKS MUST:
 *    - Open vendor search pages
 *    - Prefill dates, locations, and passengers
 *    - Let vendor resolve internal IDs
 * 
 * 4. VALIDATION:
 *    - If any required parameter is missing or undefined, BLOCK redirect
 *    - Return null instead of opening broken pages
 * 
 * 5. EXECUTION:
 *    - Frontend only does: window.open(deepLink, "_blank")
 *    - Never fetch, proxy, or iframe vendor URLs
 */

// ============================================================
// VALIDATION RESULT TYPE
// ============================================================

export interface DeepLinkResult {
  url: string | null
  error: string | null
}

// ============================================================
// VENDOR DEFINITIONS
// ============================================================

export type ServiceType = 'hotels' | 'flights' | 'buses' | 'trains'

export interface Vendor {
  id: string
  name: string
  services: ServiceType[]
  logo?: string
}

export const VENDORS: Record<string, Vendor> = {
  // Hotel vendors (ONLY service with "Book Now")
  agoda: {
    id: 'agoda',
    name: 'Agoda',
    services: ['hotels'],
  },
  makemytrip_hotels: {
    id: 'makemytrip_hotels',
    name: 'MakeMyTrip',
    services: ['hotels'],
  },
  booking: {
    id: 'booking',
    name: 'Booking.com',
    services: ['hotels'],
  },
  
  // Flight vendors ("View Flights" - Skyscanner-like search flow)
  makemytrip_flights: {
    id: 'makemytrip_flights',
    name: 'MakeMyTrip',
    services: ['flights'],
  },
  paytm_flights: {
    id: 'paytm_flights',
    name: 'Paytm',
    services: ['flights'],
  },
  skyscanner: {
    id: 'skyscanner',
    name: 'Skyscanner',
    services: ['flights'],
  },
  
  // Bus vendors ("View Buses on {Vendor}" - Form-fill search only)
  redbus: {
    id: 'redbus',
    name: 'redBus',
    services: ['buses'],
  },
  paytm_bus: {
    id: 'paytm_bus',
    name: 'Paytm Bus',
    services: ['buses'],
  },
  makemytrip_bus: {
    id: 'makemytrip_bus',
    name: 'MakeMyTrip Bus',
    services: ['buses'],
  },
  
  // Train vendors ("Check Train Availability" - Form-fill availability only)
  paytm_trains: {
    id: 'paytm_trains',
    name: 'Paytm Trains',
    services: ['trains'],
  },
  makemytrip_railways: {
    id: 'makemytrip_railways',
    name: 'MakeMyTrip Railways',
    services: ['trains'],
  },
}

/**
 * Get vendors available for a specific service
 */
export function getVendorsForService(service: ServiceType): Vendor[] {
  return Object.values(VENDORS).filter(v => v.services.includes(service))
}

// ============================================================
// PARAMETER VALIDATION HELPERS
// ============================================================

/**
 * Check if a string parameter is valid (not null, undefined, or empty)
 */
function isValidString(value: string | null | undefined): value is string {
  return typeof value === 'string' && value.trim().length > 0
}

/**
 * Check if a date string is valid (YYYY-MM-DD format)
 */
function isValidDate(dateStr: string | null | undefined): boolean {
  if (!isValidString(dateStr)) return false
  const regex = /^\d{4}-\d{2}-\d{2}$/
  if (!regex.test(dateStr)) return false
  const date = new Date(dateStr)
  return !isNaN(date.getTime())
}

/**
 * Check if IATA airport code is valid (3 uppercase letters)
 */
function isValidIATACode(code: string | null | undefined): boolean {
  if (!isValidString(code)) return false
  return /^[A-Z]{3}$/.test(code.toUpperCase())
}

// ============================================================
// DATE FORMATTERS
// ============================================================

function formatMMDDYYYY(dateStr: string): string {
  // Input: YYYY-MM-DD, Output: MMDDYYYY
  const [year, month, day] = dateStr.split('-')
  return `${month}${day}${year}`
}

function formatDDMMYYYY(dateStr: string): string {
  // Input: YYYY-MM-DD, Output: DD/MM/YYYY
  const [year, month, day] = dateStr.split('-')
  return `${day}/${month}/${year}`
}

function formatDDMMYYYYDash(dateStr: string): string {
  // Input: YYYY-MM-DD, Output: DD-MM-YYYY
  const [year, month, day] = dateStr.split('-')
  return `${day}-${month}-${year}`
}

function formatDDMMMYYYY(dateStr: string): string {
  // Input: YYYY-MM-DD, Output: DD-MMM-YYYY (e.g., 31-Dec-2025)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const [year, month, day] = dateStr.split('-')
  return `${day}-${months[parseInt(month) - 1]}-${year}`
}

function calculateNights(checkIn: string, checkOut: string): number {
  const inDate = new Date(checkIn)
  const outDate = new Date(checkOut)
  return Math.ceil((outDate.getTime() - inDate.getTime()) / (1000 * 60 * 60 * 24))
}

// ============================================================
// HOTEL DEEP LINKS
// Uses: hotel name + city (search-based, no vendor-specific IDs)
// ============================================================

export interface HotelDeepLinkParams {
  hotelName: string   // Hotel name for search
  city: string        // City name
  checkIn: string     // YYYY-MM-DD
  checkOut: string    // YYYY-MM-DD
  adults?: number
  rooms?: number
}

/**
 * Validate hotel deep link parameters
 * Returns error message if validation fails, null if valid
 */
export function validateHotelParams(params: HotelDeepLinkParams): string | null {
  if (!isValidString(params.hotelName)) {
    return 'Hotel name is required'
  }
  if (!isValidString(params.city)) {
    return 'City is required'
  }
  if (!isValidDate(params.checkIn)) {
    return 'Valid check-in date is required (YYYY-MM-DD)'
  }
  if (!isValidDate(params.checkOut)) {
    return 'Valid check-out date is required (YYYY-MM-DD)'
  }
  if (new Date(params.checkIn) >= new Date(params.checkOut)) {
    return 'Check-out date must be after check-in date'
  }
  return null
}

/**
 * MakeMyTrip Hotel Deep Link (search-based, no hotel ID required)
 * Format: https://www.makemytrip.com/hotels/hotel-listing/?city=...&searchText=...
 */
function buildMakeMyTripHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const citySlug = city.toLowerCase().replace(/\s+/g, '-')
  const checkinFormatted = formatMMDDYYYY(checkIn)
  const checkoutFormatted = formatMMDDYYYY(checkOut)
  const hotelNameEncoded = encodeURIComponent(hotelName)
  const cityEncoded = encodeURIComponent(city)
  
  // Search-based deep link - vendor resolves hotel ID internally
  return `https://www.makemytrip.com/hotels/hotel-listing/?city=${citySlug}&checkin=${checkinFormatted}&checkout=${checkoutFormatted}&roomStayQualifier=${adults}e0e${rooms > 1 ? `_${adults}e0e`.repeat(rooms - 1) : ''}&country=IN&locusType=city&searchText=${hotelNameEncoded}%20${cityEncoded}`
}

/**
 * Agoda Hotel Deep Link (search-based)
 * Format: https://www.agoda.com/search?textToSearch=...
 */
function buildAgodaHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const nights = calculateNights(checkIn, checkOut)
  const hotelNameEncoded = encodeURIComponent(hotelName)
  const cityEncoded = encodeURIComponent(city)
  
  // Search-based - Agoda resolves hotel internally
  return `https://www.agoda.com/search?city=-1&checkIn=${checkIn}&checkOut=${checkOut}&rooms=${rooms}&adults=${adults}&children=0&los=${nights}&textToSearch=${hotelNameEncoded}%20${cityEncoded}`
}

/**
 * Booking.com Hotel Deep Link (search-based)
 * Format: https://www.booking.com/searchresults.html?ss=...
 */
function buildBookingHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const hotelNameEncoded = encodeURIComponent(hotelName)
  const cityEncoded = encodeURIComponent(city)
  
  // Search-based - Booking.com resolves hotel internally
  return `https://www.booking.com/searchresults.html?ss=${hotelNameEncoded}%2C+${cityEncoded}&checkin=${checkIn}&checkout=${checkOut}&group_adults=${adults}&no_rooms=${rooms}&selected_currency=INR`
}

/**
 * Build hotel deep link with validation
 * Returns null if parameters are invalid - BLOCKS redirect
 */
export function buildHotelDeepLink(vendorId: string, params: HotelDeepLinkParams): DeepLinkResult {
  const validationError = validateHotelParams(params)
  if (validationError) {
    return { url: null, error: validationError }
  }
  
  let url: string
  switch (vendorId) {
    case 'makemytrip_hotels':
      url = buildMakeMyTripHotelUrl(params)
      break
    case 'agoda':
      url = buildAgodaHotelUrl(params)
      break
    case 'booking':
      url = buildBookingHotelUrl(params)
      break
    default:
      url = buildBookingHotelUrl(params)
  }
  
  return { url, error: null }
}

// ============================================================
// FLIGHT DEEP LINKS
// ============================================================

export interface FlightDeepLinkParams {
  origin: string      // IATA code
  destination: string // IATA code
  departDate: string  // YYYY-MM-DD
  returnDate?: string // YYYY-MM-DD (for round trip)
  adults?: number
  children?: number
  infants?: number
  cabinClass?: 'economy' | 'business' | 'first'
}

/**
 * MakeMyTrip Flight Deep Link (search level only)
 * Format: https://www.makemytrip.com/flight/search?itinerary=...
 */
export function buildMakeMyTripFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, returnDate, adults = 1, children = 0, infants = 0 } = params
  
  const dateFormatted = formatDDMMYYYY(departDate)
  const tripType = returnDate ? 'R' : 'O'
  const intl = origin.length === 3 && destination.length === 3 ? 'false' : 'true'
  
  let itinerary = `${origin}-${destination}-${dateFormatted}`
  if (returnDate) {
    itinerary += `_${destination}-${origin}-${formatDDMMYYYY(returnDate)}`
  }
  
  return `https://www.makemytrip.com/flight/search?itinerary=${itinerary}&tripType=${tripType}&paxType=A-${adults}_C-${children}_I-${infants}&intl=${intl}&cabinClass=E`
}

/**
 * Paytm Flight Deep Link
 * Format: https://tickets.paytm.com/flights/search?from=...
 */
export function buildPaytmFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, adults = 1, children = 0, infants = 0 } = params
  
  return `https://tickets.paytm.com/flights/search?from=${origin}&to=${destination}&date=${departDate}&adults=${adults}&children=${children}&infants=${infants}&class=economy`
}

/**
 * Skyscanner Flight Deep Link (Search results page)
 * Format: https://www.skyscanner.co.in/transport/flights/...
 */
export function buildSkyscannerFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, adults = 1, children = 0, infants = 0 } = params
  
  // Skyscanner format: YYMMDD
  const [year, month, day] = departDate.split('-')
  const dateFormatted = `${year.slice(2)}${month}${day}`
  
  // Skyscanner cabin class: economy, premiumeconomy, business, first
  const cabinClass = 'economy'
  
  return `https://www.skyscanner.co.in/transport/flights/${origin.toLowerCase()}/${destination.toLowerCase()}/${dateFormatted}/?adults=${adults}&children=${children}&infants=${infants}&cabinclass=${cabinClass}&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false`
}

/**
 * Build flight deep link for any vendor
 * NOTE: Search-level links only - no reviewDetails, itineraryId, rKey, or session URLs
 */
export function buildFlightDeepLink(vendorId: string, params: FlightDeepLinkParams): string {
  switch (vendorId) {
    case 'makemytrip_flights':
      return buildMakeMyTripFlightUrl(params)
    case 'paytm_flights':
      return buildPaytmFlightUrl(params)
    case 'skyscanner':
      return buildSkyscannerFlightUrl(params)
    default:
      return buildMakeMyTripFlightUrl(params)
  }
}

// ============================================================
// BUS DEEP LINKS
// ============================================================

export interface BusDeepLinkParams {
  fromCity: string
  toCity: string
  date: string // YYYY-MM-DD
}

/**
 * redBus Deep Link
 * Format: https://www.redbus.in/search?fromCityName=...
 */
export function buildRedBusUrl(params: BusDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const dateFormatted = formatDDMMMYYYY(date)
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://www.redbus.in/search?fromCityName=${fromEncoded}&toCityName=${toEncoded}&onward=${dateFormatted}`
}

/**
 * Paytm Bus Deep Link
 * Format: https://tickets.paytm.com/bus/search?source=...
 */
export function buildPaytmBusUrl(params: BusDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://tickets.paytm.com/bus/search?source=${fromEncoded}&destination=${toEncoded}&date=${date}`
}

/**
 * MakeMyTrip Bus Deep Link
 * Format: https://www.makemytrip.com/bus-tickets/...
 */
export function buildMakeMyTripBusUrl(params: BusDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  // MMT Bus format: city names as slugs
  const fromSlug = fromCity.toLowerCase().replace(/\s+/g, '-')
  const toSlug = toCity.toLowerCase().replace(/\s+/g, '-')
  const dateFormatted = formatDDMMYYYY(date)
  
  return `https://www.makemytrip.com/bus-tickets/${fromSlug}-${toSlug}-bus.html?departDate=${dateFormatted}`
}

/**
 * Build bus deep link for any vendor
 * NOTE: Form-fill search only - no direct seat or payment redirects
 */
export function buildBusDeepLink(vendorId: string, params: BusDeepLinkParams): string {
  switch (vendorId) {
    case 'redbus':
      return buildRedBusUrl(params)
    case 'paytm_bus':
      return buildPaytmBusUrl(params)
    case 'makemytrip_bus':
      return buildMakeMyTripBusUrl(params)
    default:
      return buildRedBusUrl(params)
  }
}

// ============================================================
// TRAIN DEEP LINKS
// ============================================================

export interface TrainDeepLinkParams {
  fromStation: string // Station name or code
  toStation: string   // Station name or code
  fromCity: string    // City name
  toCity: string      // City name
  date: string        // YYYY-MM-DD
}

/**
 * Paytm Trains Deep Link (search only)
 * Format: https://tickets.paytm.com/trains/search?from=...
 */
export function buildPaytmTrainsUrl(params: TrainDeepLinkParams): string {
  const { fromStation, toStation, date } = params
  
  const fromEncoded = encodeURIComponent(fromStation)
  const toEncoded = encodeURIComponent(toStation)
  
  return `https://tickets.paytm.com/trains/search?from=${fromEncoded}&to=${toEncoded}&date=${date}`
}

/**
 * MakeMyTrip Railways Deep Link
 * Format: https://www.makemytrip.com/railways/search?fromCity=...
 */
export function buildMakeMyTripRailwaysUrl(params: TrainDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const dateFormatted = formatDDMMYYYYDash(date)
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://www.makemytrip.com/railways/search?fromCity=${fromEncoded}&toCity=${toEncoded}&date=${dateFormatted}`
}

/**
 * Build train deep link for any vendor
 * NOTE: Form-fill availability only - no payment-page redirects
 */
export function buildTrainDeepLink(vendorId: string, params: TrainDeepLinkParams): string {
  switch (vendorId) {
    case 'paytm_trains':
      return buildPaytmTrainsUrl(params)
    case 'makemytrip_railways':
      return buildMakeMyTripRailwaysUrl(params)
    default:
      return buildPaytmTrainsUrl(params)
  }
}

// ============================================================
// LEGACY COMPATIBILITY (for existing code)
// ============================================================

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
  hotelName?: string
  hotelId?: string
}

/**
 * Legacy: Build Aviasales flight URL (uses MakeMyTrip instead)
 */
export function buildAviasalesFlightUrl(params: FlightSearchParams): string {
  return buildMakeMyTripFlightUrl({
    origin: params.origin,
    destination: params.destination,
    departDate: params.departDate,
    returnDate: params.returnDate,
    adults: params.adults,
    children: params.children,
    infants: params.infants,
  })
}

/**
 * Legacy: Build Aviasales hotel URL (uses Booking.com instead)
 */
export function buildAviasalesHotelUrl(params: HotelSearchParams): string {
  return buildBookingHotelUrl({
    hotelName: params.hotelName || params.city,
    city: params.city,
    checkIn: params.checkIn,
    checkOut: params.checkOut,
    adults: params.adults,
  })
}

/**
 * Legacy: Build hotel-specific URL
 */
export function buildHotelSpecificUrl(
  hotelName: string,
  city: string,
  checkIn: string,
  checkOut: string,
  adults: number = 2
): string {
  return buildBookingHotelUrl({ hotelName, city, checkIn, checkOut, adults })
}

/**
 * Log affiliate click (fire-and-forget)
 */
export async function logAffiliateClick(
  provider: string,
  route: string,
  offerId: string,
  price?: number
): Promise<void> {
  try {
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
      keepalive: true,
    }).catch(() => {})
  } catch {
    // Silently fail
  }
}
