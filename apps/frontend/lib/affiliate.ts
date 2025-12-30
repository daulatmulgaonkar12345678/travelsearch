/**
 * Vendor Deep Link Builder
 * 
 * CRITICAL RULES:
 * 1. Use SEARCH-LEVEL deep links only (no session tokens, no encoded IDs)
 * 2. Each vendor only supports specific services
 * 3. Frontend only does: window.open(deepLink, "_blank")
 * 4. Never fetch, proxy, or iframe vendor URLs
 * 5. If a vendor link is unstable, disable the vendor instead of guessing
 * 
 * SUPPORTED FLOWS & VENDORS (LOCKED):
 * 
 * HOTELS (Direct Booking - "Book Now"):
 *   - Agoda, MakeMyTrip Hotels, Booking.com
 *   - Hotel-specific deep links with dates, guests, rooms prefilled
 * 
 * FLIGHTS (Search Flow - "View Flights"):
 *   - MakeMyTrip Flights, Paytm Flights, Skyscanner
 *   - Search-level deep links only (route, date, passengers, cabin)
 * 
 * BUS (Form-Fill Search - "View Buses on {Vendor}"):
 *   - redBus, Paytm Bus, MakeMyTrip Bus
 *   - Search-level deep links (source, destination, date)
 * 
 * TRAIN (Availability Search - "Check Train Availability"):
 *   - Paytm Trains, MakeMyTrip Railways
 *   - Search-level deep links (from, to, date)
 */

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
// ============================================================

export interface HotelDeepLinkParams {
  hotelName: string
  city: string
  checkIn: string  // YYYY-MM-DD
  checkOut: string // YYYY-MM-DD
  adults?: number
  rooms?: number
  hotelId?: string
  cityCode?: string
}

/**
 * MakeMyTrip Hotel Deep Link
 * Format: https://www.makemytrip.com/hotels/hotel-details/?hotelId=...
 * 
 * Note: Without hotel ID, falls back to search
 */
export function buildMakeMyTripHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1, cityCode } = params
  
  // Use city search (hotel-details requires specific hotelId from MMT)
  const citySlug = city.toLowerCase().replace(/\s+/g, '-')
  const checkinFormatted = formatMMDDYYYY(checkIn)
  const checkoutFormatted = formatMMDDYYYY(checkOut)
  
  // Search-level deep link with hotel name in query
  const hotelNameEncoded = encodeURIComponent(hotelName)
  
  return `https://www.makemytrip.com/hotels/hotel-listing/?city=${cityCode || citySlug}&checkin=${checkinFormatted}&checkout=${checkoutFormatted}&roomStayQualifier=${adults}e0e&locusId=CTDEL&country=IN&locusType=city&searchText=${hotelNameEncoded}`
}

/**
 * Agoda Hotel Deep Link
 * Format: https://www.agoda.com/search?city=...
 */
export function buildAgodaHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const nights = calculateNights(checkIn, checkOut)
  const hotelNameEncoded = encodeURIComponent(hotelName)
  const cityEncoded = encodeURIComponent(city)
  
  return `https://www.agoda.com/search?city=-1&checkIn=${checkIn}&checkOut=${checkOut}&rooms=${rooms}&adults=${adults}&children=0&los=${nights}&textToSearch=${hotelNameEncoded}%20${cityEncoded}`
}

/**
 * Booking.com Hotel Deep Link
 * Format: https://www.booking.com/searchresults.html?ss=...
 */
export function buildBookingHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const hotelNameEncoded = encodeURIComponent(hotelName)
  const cityEncoded = encodeURIComponent(city)
  
  return `https://www.booking.com/searchresults.html?ss=${hotelNameEncoded}%2C+${cityEncoded}&checkin=${checkIn}&checkout=${checkOut}&group_adults=${adults}&no_rooms=${rooms}&selected_currency=INR`
}

/**
 * Build hotel deep link for any vendor
 */
export function buildHotelDeepLink(vendorId: string, params: HotelDeepLinkParams): string {
  switch (vendorId) {
    case 'makemytrip_hotels':
      return buildMakeMyTripHotelUrl(params)
    case 'agoda':
      return buildAgodaHotelUrl(params)
    case 'booking':
      return buildBookingHotelUrl(params)
    default:
      // Fallback to Booking.com
      return buildBookingHotelUrl(params)
  }
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
 * Build flight deep link for any vendor
 */
export function buildFlightDeepLink(vendorId: string, params: FlightDeepLinkParams): string {
  switch (vendorId) {
    case 'makemytrip_flights':
      return buildMakeMyTripFlightUrl(params)
    case 'paytm_flights':
      return buildPaytmFlightUrl(params)
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
 * Build bus deep link for any vendor
 */
export function buildBusDeepLink(vendorId: string, params: BusDeepLinkParams): string {
  switch (vendorId) {
    case 'redbus':
      return buildRedBusUrl(params)
    case 'paytm_bus':
      return buildPaytmBusUrl(params)
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
