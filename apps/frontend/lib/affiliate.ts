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
  isPrimary?: boolean
  priority?: number // Lower number = higher priority
}

export const VENDORS: Record<string, Vendor> = {
  // ============================================================
  // HOTEL VENDORS - Priority Order: Booking.com (PRIMARY), Agoda, MakeMyTrip
  // REMOVED: Udchalo (discontinued)
  // ============================================================
  booking: {
    id: 'booking',
    name: 'Booking.com',
    services: ['hotels'],
    isPrimary: true,
    priority: 1,
  },
  agoda: {
    id: 'agoda',
    name: 'Agoda',
    services: ['hotels'],
    priority: 2,
  },
  makemytrip_hotels: {
    id: 'makemytrip_hotels',
    name: 'MakeMyTrip',
    services: ['hotels'],
    priority: 3,
  },
  
  // ============================================================
  // FLIGHT VENDORS - Skyscanner (PRIMARY meta-search)
  // REMOVED: Udchalo (discontinued), Paytm (unstable), Ixigo (payment-level deep links)
  // ============================================================
  skyscanner: {
    id: 'skyscanner',
    name: 'Skyscanner',
    services: ['flights'],
    isPrimary: true,
    priority: 1,
  },
  makemytrip_flights: {
    id: 'makemytrip_flights',
    name: 'MakeMyTrip',
    services: ['flights'],
    priority: 2,
  },
  goibibo_flights: {
    id: 'goibibo_flights',
    name: 'Goibibo',
    services: ['flights'],
    priority: 3,
  },
  easemytrip_flights: {
    id: 'easemytrip_flights',
    name: 'EaseMyTrip',
    services: ['flights'],
    priority: 4,
  },
  
  // ============================================================
  // BUS VENDORS - MSRTC (PRIMARY for Maharashtra), redBus, Paytm Bus
  // REMOVED: Udchalo (discontinued), Ixigo (unstable deep links)
  // ============================================================
  msrtc: {
    id: 'msrtc',
    name: 'MSRTC',
    services: ['buses'],
    isPrimary: true,
    priority: 1,
  },
  redbus: {
    id: 'redbus',
    name: 'redBus',
    services: ['buses'],
    priority: 2,
  },
  paytm_bus: {
    id: 'paytm_bus',
    name: 'Paytm Bus',
    services: ['buses'],
    priority: 3,
  },
  
  // ============================================================
  // TRAIN VENDORS - IRCTC (PRIMARY official), MakeMyTrip, Goibibo
  // REMOVED: Udchalo (discontinued), Ixigo (moved to lower priority)
  // ============================================================
  irctc: {
    id: 'irctc',
    name: 'IRCTC',
    services: ['trains'],
    isPrimary: true,
    priority: 1,
  },
  makemytrip_railways: {
    id: 'makemytrip_railways',
    name: 'MakeMyTrip',
    services: ['trains'],
    priority: 2,
  },
  goibibo_trains: {
    id: 'goibibo_trains',
    name: 'Goibibo',
    services: ['trains'],
    priority: 3,
  },
}

/**
 * Get vendors available for a specific service
 * Returns vendors sorted by priority (primary first, then by priority number)
 */
export function getVendorsForService(service: ServiceType): Vendor[] {
  const vendors = Object.values(VENDORS).filter(v => v.services.includes(service))
  return vendors.sort((a, b) => {
    // Primary vendor always first
    if (a.isPrimary && !b.isPrimary) return -1
    if (!a.isPrimary && b.isPrimary) return 1
    // Then sort by priority number (lower = higher priority)
    const priorityA = a.priority ?? 999
    const priorityB = b.priority ?? 999
    return priorityA - priorityB
  })
}

/**
 * Get the primary (default) vendor for a service
 */
export function getPrimaryVendor(service: ServiceType): Vendor | undefined {
  return Object.values(VENDORS).find(v => v.services.includes(service) && v.isPrimary)
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
 * Goibibo Hotel Deep Link (search-based)
 * Format: https://www.goibibo.com/hotels/...
 */
function buildGoibiboHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const citySlug = city.toLowerCase().replace(/\s+/g, '-')
  const hotelNameEncoded = encodeURIComponent(hotelName)
  
  return `https://www.goibibo.com/hotels/search/?cc=IN&ci=${checkIn}&co=${checkOut}&r=1-${adults}-0&q=${hotelNameEncoded}%20${citySlug}`
}

/**
 * EaseMyTrip Hotel Deep Link (search-based)
 * Format: https://www.easemytrip.com/hotels/...
 */
function buildEaseMyTripHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const citySlug = city.toLowerCase().replace(/\s+/g, '-')
  const hotelNameEncoded = encodeURIComponent(hotelName)
  const checkInFormatted = formatDDMMYYYYDash(checkIn)
  const checkOutFormatted = formatDDMMYYYYDash(checkOut)
  
  return `https://www.easemytrip.com/hotels/search.html?city=${citySlug}&checkin=${checkInFormatted}&checkout=${checkOutFormatted}&rooms=${rooms}&adults=${adults}&q=${hotelNameEncoded}`
}

/**
 * Udchalo Hotel Deep Link (search-based) - Priority booking
 * Format: https://www.udchalo.com/hotels/search?...
 */
function buildUdchaloHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const cityEncoded = encodeURIComponent(city)
  const hotelNameEncoded = encodeURIComponent(hotelName)
  
  return `https://www.udchalo.com/hotels/search?city=${cityEncoded}&checkin=${checkIn}&checkout=${checkOut}&rooms=${rooms}&adults=${adults}&q=${hotelNameEncoded}`
}

/**
 * Skyscanner Hotels Deep Link (meta search)
 * Format: https://www.skyscanner.co.in/hotels/search?...
 */
function buildSkyscannerHotelUrl(params: HotelDeepLinkParams): string {
  const { hotelName, city, checkIn, checkOut, adults = 2, rooms = 1 } = params
  
  const cityEncoded = encodeURIComponent(city)
  const hotelNameEncoded = encodeURIComponent(hotelName)
  
  return `https://www.skyscanner.co.in/hotels/search?entity_id=&checkin=${checkIn}&checkout=${checkOut}&rooms=${rooms}&adults=${adults}&query=${hotelNameEncoded}%20${cityEncoded}`
}

/**
 * Build hotel deep link with validation
 * Returns null if parameters are invalid - BLOCKS redirect
 * Default: Booking.com (PRIMARY)
 * REMOVED: Udchalo (discontinued)
 */
export function buildHotelDeepLink(vendorId: string, params: HotelDeepLinkParams): DeepLinkResult {
  const validationError = validateHotelParams(params)
  if (validationError) {
    return { url: null, error: validationError }
  }
  
  let url: string
  switch (vendorId) {
    case 'booking':
      url = buildBookingHotelUrl(params)
      break
    case 'agoda':
      url = buildAgodaHotelUrl(params)
      break
    case 'makemytrip_hotels':
      url = buildMakeMyTripHotelUrl(params)
      break
    default:
      // Booking.com is PRIMARY for hotels
      url = buildBookingHotelUrl(params)
  }
  
  return { url, error: null }
}

// ============================================================
// FLIGHT DEEP LINKS
// Uses: IATA airport codes only (DEL, BOM, etc.)
// ============================================================

export interface FlightDeepLinkParams {
  origin: string      // IATA code (3 letters)
  destination: string // IATA code (3 letters)
  departDate: string  // YYYY-MM-DD
  returnDate?: string // YYYY-MM-DD (for round trip)
  adults?: number
  children?: number
  infants?: number
  cabinClass?: 'economy' | 'business' | 'first'
}

/**
 * Validate flight deep link parameters
 * Returns error message if validation fails, null if valid
 */
export function validateFlightParams(params: FlightDeepLinkParams): string | null {
  if (!isValidString(params.origin)) {
    return 'Origin airport code is required'
  }
  if (!isValidIATACode(params.origin)) {
    return `Invalid origin airport code: ${params.origin} (must be 3 letters)`
  }
  if (!isValidString(params.destination)) {
    return 'Destination airport code is required'
  }
  if (!isValidIATACode(params.destination)) {
    return `Invalid destination airport code: ${params.destination} (must be 3 letters)`
  }
  if (!isValidDate(params.departDate)) {
    return 'Valid departure date is required (YYYY-MM-DD)'
  }
  if (params.returnDate && !isValidDate(params.returnDate)) {
    return 'Invalid return date format (YYYY-MM-DD)'
  }
  return null
}

/**
 * MakeMyTrip Flight Deep Link (search level only, IATA codes)
 * Format: https://www.makemytrip.com/flight/search?itinerary=DEL-BOM-...
 */
function buildMakeMyTripFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, returnDate, adults = 1, children = 0, infants = 0 } = params
  
  const dateFormatted = formatDDMMYYYY(departDate)
  const tripType = returnDate ? 'R' : 'O'
  
  let itinerary = `${origin.toUpperCase()}-${destination.toUpperCase()}-${dateFormatted}`
  if (returnDate) {
    itinerary += `_${destination.toUpperCase()}-${origin.toUpperCase()}-${formatDDMMYYYY(returnDate)}`
  }
  
  return `https://www.makemytrip.com/flight/search?itinerary=${itinerary}&tripType=${tripType}&paxType=A-${adults}_C-${children}_I-${infants}&intl=false&cabinClass=E`
}

/**
 * Skyscanner Flight Deep Link (IATA codes) - PRIMARY
 * Format: https://www.skyscanner.co.in/transport/flights/del/bom/...
 */
function buildSkyscannerFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, adults = 1, children = 0, infants = 0 } = params
  
  // Skyscanner format: YYMMDD
  const [year, month, day] = departDate.split('-')
  const dateFormatted = `${year.slice(2)}${month}${day}`
  
  return `https://www.skyscanner.co.in/transport/flights/${origin.toLowerCase()}/${destination.toLowerCase()}/${dateFormatted}/?adults=${adults}&children=${children}&infants=${infants}&cabinclass=economy&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false`
}

/**
 * Goibibo Flight Deep Link (IATA codes)
 * Format: https://www.goibibo.com/flights/...
 */
function buildGoibiboFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, adults = 1, children = 0, infants = 0 } = params
  
  const dateFormatted = departDate.replace(/-/g, '')
  
  return `https://www.goibibo.com/flights/air-${origin.toUpperCase()}-${destination.toUpperCase()}-${dateFormatted}-${adults}-${children}-${infants}-E-D`
}

/**
 * EaseMyTrip Flight Deep Link (IATA codes)
 * Format: https://www.easemytrip.com/flights/...
 */
function buildEaseMyTripFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, adults = 1, children = 0, infants = 0 } = params
  
  const dateFormatted = formatDDMMYYYYDash(departDate)
  
  return `https://www.easemytrip.com/flights/${origin.toUpperCase()}-${destination.toUpperCase()}-${dateFormatted}/?adults=${adults}&child=${children}&infant=${infants}&class=E&trip=oneway`
}

/**
 * Udchalo Flight Deep Link (IATA codes) - Defense/Govt priority booking
 * Format: https://www.udchalo.com/flights/search?...
 */
function buildUdchaloFlightUrl(params: FlightDeepLinkParams): string {
  const { origin, destination, departDate, adults = 1, children = 0, infants = 0 } = params
  
  return `https://www.udchalo.com/flights/search?from=${origin.toUpperCase()}&to=${destination.toUpperCase()}&date=${departDate}&adults=${adults}&children=${children}&infants=${infants}&class=economy`
}

/**
 * Build flight deep link with validation
 * Returns null if parameters are invalid - BLOCKS redirect
 * Default: Skyscanner (PRIMARY)
 * REMOVED: Udchalo (discontinued), Ixigo (payment-level deep links unstable)
 */
export function buildFlightDeepLink(vendorId: string, params: FlightDeepLinkParams): DeepLinkResult {
  const validationError = validateFlightParams(params)
  if (validationError) {
    return { url: null, error: validationError }
  }
  
  let url: string
  switch (vendorId) {
    case 'skyscanner':
      url = buildSkyscannerFlightUrl(params)
      break
    case 'makemytrip_flights':
      url = buildMakeMyTripFlightUrl(params)
      break
    case 'goibibo_flights':
      url = buildGoibiboFlightUrl(params)
      break
    case 'easemytrip_flights':
      url = buildEaseMyTripFlightUrl(params)
      break
    default:
      // Skyscanner is PRIMARY for flights
      url = buildSkyscannerFlightUrl(params)
  }
  
  return { url, error: null }
}

// ============================================================
// BUS DEEP LINKS
// Uses: City names only (no vendor-specific IDs)
// ============================================================

export interface BusDeepLinkParams {
  fromCity: string  // City name (e.g., "Pune", "Mumbai")
  toCity: string    // City name
  date: string      // YYYY-MM-DD
}

/**
 * Validate bus deep link parameters
 * Returns error message if validation fails, null if valid
 */
export function validateBusParams(params: BusDeepLinkParams): string | null {
  if (!isValidString(params.fromCity)) {
    return 'Origin city is required'
  }
  if (!isValidString(params.toCity)) {
    return 'Destination city is required'
  }
  if (!isValidDate(params.date)) {
    return 'Valid travel date is required (YYYY-MM-DD)'
  }
  return null
}

/**
 * redBus Deep Link (city names, vendor resolves IDs)
 * Format: https://www.redbus.in/search?fromCityName=Pune&toCityName=Mumbai...
 */
function buildRedBusUrl(params: BusDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const dateFormatted = formatDDMMMYYYY(date)
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://www.redbus.in/search?fromCityName=${fromEncoded}&toCityName=${toEncoded}&onward=${dateFormatted}`
}

/**
 * Goibibo Bus Deep Link (city names)
 * Format: https://www.goibibo.com/bus/...
 */
function buildGoibiboBusUrl(params: BusDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://www.goibibo.com/bus/search/?src=${fromEncoded}&dest=${toEncoded}&dt=${date}`
}

/**
 * EaseMyTrip Bus Deep Link (city names)
 * Format: https://www.easemytrip.com/bus/...
 */
function buildEaseMyTripBusUrl(params: BusDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const fromSlug = fromCity.toLowerCase().replace(/\s+/g, '-')
  const toSlug = toCity.toLowerCase().replace(/\s+/g, '-')
  const dateFormatted = formatDDMMYYYYDash(date)
  
  return `https://www.easemytrip.com/bus/${fromSlug}-to-${toSlug}-bus.html?date=${dateFormatted}`
}

// REMOVED: Ixigo Bus (unstable deep links)

/**
 * Build bus deep link with validation
 * Returns null if parameters are invalid - BLOCKS redirect
 * REMOVED: Ixigo (unstable deep links)
 */
export function buildBusDeepLink(vendorId: string, params: BusDeepLinkParams): DeepLinkResult {
  const validationError = validateBusParams(params)
  if (validationError) {
    return { url: null, error: validationError }
  }
  
  let url: string
  switch (vendorId) {
    case 'redbus':
      url = buildRedBusUrl(params)
      break
    case 'goibibo_bus':
      url = buildGoibiboBusUrl(params)
      break
    case 'easemytrip_bus':
      url = buildEaseMyTripBusUrl(params)
      break
    default:
      // redBus is PRIMARY for buses
      url = buildRedBusUrl(params)
  }
  
  return { url, error: null }
}

// ============================================================
// TRAIN DEEP LINKS
// Uses: IRCTC station codes or city names (no vendor-specific IDs)
// ============================================================

export interface TrainDeepLinkParams {
  fromStation: string // Station code (e.g., CSMT, NDLS) or city name
  toStation: string   // Station code or city name
  fromCity: string    // City name for display/fallback
  toCity: string      // City name for display/fallback
  date: string        // YYYY-MM-DD
}

/**
 * Validate train deep link parameters
 * Returns error message if validation fails, null if valid
 */
export function validateTrainParams(params: TrainDeepLinkParams): string | null {
  if (!isValidString(params.fromStation) && !isValidString(params.fromCity)) {
    return 'Origin station or city is required'
  }
  if (!isValidString(params.toStation) && !isValidString(params.toCity)) {
    return 'Destination station or city is required'
  }
  if (!isValidDate(params.date)) {
    return 'Valid travel date is required (YYYY-MM-DD)'
  }
  return null
}

/**
 * Ixigo Trains Deep Link (station codes) - PRIMARY
 * Format: https://www.ixigo.com/search/result/train/...
 */
function buildIxigoTrainsUrl(params: TrainDeepLinkParams): string {
  const { fromStation, toStation, date } = params
  
  const fromEncoded = encodeURIComponent(fromStation)
  const toEncoded = encodeURIComponent(toStation)
  const dateFormatted = formatDDMMYYYY(date)
  
  return `https://www.ixigo.com/search/result/train/${fromEncoded}/${toEncoded}/${dateFormatted}`
}

/**
 * MakeMyTrip Railways Deep Link (city names)
 * Format: https://www.makemytrip.com/railways/search?fromCity=Mumbai&toCity=Pune...
 */
function buildMakeMyTripRailwaysUrl(params: TrainDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const dateFormatted = formatDDMMYYYYDash(date)
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://www.makemytrip.com/railways/search?fromCity=${fromEncoded}&toCity=${toEncoded}&date=${dateFormatted}`
}

/**
 * Goibibo Trains Deep Link (city names)
 * Format: https://www.goibibo.com/trains/...
 */
function buildGoibiboTrainsUrl(params: TrainDeepLinkParams): string {
  const { fromCity, toCity, date } = params
  
  const fromEncoded = encodeURIComponent(fromCity)
  const toEncoded = encodeURIComponent(toCity)
  
  return `https://www.goibibo.com/trains/search/?src=${fromEncoded}&dest=${toEncoded}&dt=${date}`
}

/**
 * Build train deep link with validation
 * Returns null if parameters are invalid - BLOCKS redirect
 */
export function buildTrainDeepLink(vendorId: string, params: TrainDeepLinkParams): DeepLinkResult {
  const validationError = validateTrainParams(params)
  if (validationError) {
    return { url: null, error: validationError }
  }
  
  let url: string
  switch (vendorId) {
    case 'ixigo_trains':
      url = buildIxigoTrainsUrl(params)
      break
    case 'makemytrip_railways':
      url = buildMakeMyTripRailwaysUrl(params)
      break
    case 'goibibo_trains':
      url = buildGoibiboTrainsUrl(params)
      break
    default:
      // Ixigo is PRIMARY for trains
      url = buildIxigoTrainsUrl(params)
  }
  
  return { url, error: null }
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
