/**
 * Internal Linking Components for SEO - Enhanced with Images
 * 
 * Features:
 * - Static destination images (WebP preferred)
 * - Lazy loading for performance (LCP-friendly)
 * - Semantic HTML (section, h2, article)
 * - Proper alt text for accessibility/SEO
 * - Smart date handling (tomorrow by default)
 * - Limited to 6-8 items for performance
 * 
 * UX PRINCIPLE:
 * User clicks route → SEO page with pre-filled search bar → adjust date → search
 * 
 * Image Storage:
 * - Images stored in /public/images/flights/ and /public/images/hotels/
 * - Naming convention: {route-slug}.webp, {city}.webp
 * - Recommended size: 400x300px for cards
 */

'use client'

import Link from 'next/link'
import Image from 'next/image'

// ============================================================================
// DATA STRUCTURES
// ============================================================================

export interface FlightRouteData {
  slug: string
  label: string
  origin: string
  destination: string
  originCode: string
  destinationCode: string
  /** Image filename in /public/images/routes/ (without path) */
  image?: string
  /** Short description for SEO */
  description?: string
}

export interface HotelDestinationData {
  slug: string
  city: string
  label: string
  /** Image filename in /public/images/destinations/ (without path) */
  image?: string
  /** Short description for SEO */
  description?: string
}

// Popular flight routes data
export const POPULAR_FLIGHT_ROUTES: FlightRouteData[] = [
  { 
    slug: 'delhi-to-mumbai', 
    label: 'Delhi to Mumbai',
    origin: 'Delhi',
    destination: 'Mumbai',
    originCode: 'DEL',
    destinationCode: 'BOM',
    image: 'delhi-to-mumbai.webp',
    description: 'One of India\'s busiest air routes connecting the capital to the financial hub'
  },
  { 
    slug: 'mumbai-to-bangalore', 
    label: 'Mumbai to Bangalore',
    origin: 'Mumbai',
    destination: 'Bangalore',
    originCode: 'BOM',
    destinationCode: 'BLR',
    image: 'mumbai-to-bangalore.webp',
    description: 'Connect the financial capital to India\'s tech hub'
  },
  { 
    slug: 'delhi-to-goa', 
    label: 'Delhi to Goa',
    origin: 'Delhi',
    destination: 'Goa',
    originCode: 'DEL',
    destinationCode: 'GOI',
    image: 'delhi-to-goa.webp',
    description: 'Popular route to India\'s favorite beach destination'
  },
  { 
    slug: 'bangalore-to-delhi', 
    label: 'Bangalore to Delhi',
    origin: 'Bangalore',
    destination: 'Delhi',
    originCode: 'BLR',
    destinationCode: 'DEL',
    image: 'bangalore-to-delhi.webp',
    description: 'Tech hub to national capital corridor'
  },
  { 
    slug: 'mumbai-to-goa', 
    label: 'Mumbai to Goa',
    origin: 'Mumbai',
    destination: 'Goa',
    originCode: 'BOM',
    destinationCode: 'GOI',
    image: 'mumbai-to-goa.webp',
    description: 'Quick getaway from Mumbai to beach paradise'
  },
  { 
    slug: 'hyderabad-to-bangalore', 
    label: 'Hyderabad to Bangalore',
    origin: 'Hyderabad',
    destination: 'Bangalore',
    originCode: 'HYD',
    destinationCode: 'BLR',
    image: 'hyderabad-to-bangalore.webp',
    description: 'Connect two of South India\'s tech hubs'
  },
]

// Popular hotel destinations data
export const POPULAR_HOTEL_DESTINATIONS: HotelDestinationData[] = [
  { 
    slug: 'mumbai', 
    city: 'Mumbai',
    label: 'Hotels in Mumbai',
    image: 'mumbai.webp',
    description: 'Find hotels in India\'s financial capital'
  },
  { 
    slug: 'delhi', 
    city: 'Delhi',
    label: 'Hotels in Delhi',
    image: 'delhi.webp',
    description: 'Stay in India\'s historic capital city'
  },
  { 
    slug: 'goa', 
    city: 'Goa',
    label: 'Hotels in Goa',
    image: 'goa.webp',
    description: 'Beach resorts and hotels in Goa'
  },
  { 
    slug: 'bangalore', 
    city: 'Bangalore',
    label: 'Hotels in Bangalore',
    image: 'bangalore.webp',
    description: 'Hotels in India\'s garden city'
  },
  { 
    slug: 'jaipur', 
    city: 'Jaipur',
    label: 'Hotels in Jaipur',
    image: 'jaipur.webp',
    description: 'Heritage hotels in the Pink City'
  },
  { 
    slug: 'chennai', 
    city: 'Chennai',
    label: 'Hotels in Chennai',
    image: 'chennai.webp',
    description: 'Hotels in South India\'s cultural hub'
  },
]

// Popular train routes data (static for now)
// CRITICAL: Use CITY_ALL tokens for multi-station cities
// Backend requires station codes or _ALL tokens (NOT city names)
export const POPULAR_TRAIN_ROUTES = [
  { 
    slug: 'mumbai-delhi', 
    label: 'Mumbai → Delhi',
    origin: 'MUMBAI_ALL',        // Backend-compatible token
    destination: 'DELHI_ALL',     // Backend-compatible token
    originCity: 'Mumbai',         // Display name
    destinationCity: 'Delhi',     // Display name
    description: 'One of India\'s busiest rail corridors'
  },
  { 
    slug: 'delhi-jaipur', 
    label: 'Delhi → Jaipur',
    origin: 'DELHI_ALL',
    destination: 'JAIPUR_ALL',
    originCity: 'Delhi',
    destinationCity: 'Jaipur',
    description: 'Popular tourist route to the Pink City'
  },
  { 
    slug: 'bangalore-chennai', 
    label: 'Bangalore → Chennai',
    origin: 'BANGALORE_ALL',
    destination: 'CHENNAI_ALL',
    originCity: 'Bangalore',
    destinationCity: 'Chennai',
    description: 'Connect two South Indian metro cities'
  },
  { 
    slug: 'mumbai-pune', 
    label: 'Mumbai → Pune',
    origin: 'MUMBAI_ALL',
    destination: 'PUNE',
    originCity: 'Mumbai',
    destinationCity: 'Pune',
    description: 'Frequent trains on this short route'
  },
  { 
    slug: 'kolkata-delhi', 
    label: 'Kolkata → Delhi',
    origin: 'KOLKATA_ALL',
    destination: 'DELHI_ALL',
    originCity: 'Kolkata',
    destinationCity: 'Delhi',
    description: 'Major East-North corridor'
  },
  { 
    slug: 'hyderabad-bangalore', 
    label: 'Hyderabad → Bangalore',
    origin: 'HYDERABAD_ALL',
    destination: 'BANGALORE_ALL',
    originCity: 'Hyderabad',
    destinationCity: 'Bangalore',
    description: 'Connect Deccan and South India'
  },
]

// Popular bus routes data (static for now)
// CRITICAL: Use CITY NAMES only - no stations, no pickup points
export const POPULAR_BUS_ROUTES = [
  { 
    slug: 'pune-mumbai', 
    label: 'Pune → Mumbai',
    originCity: 'Pune',
    destinationCity: 'Mumbai',
    description: 'Most frequent bus route in Maharashtra'
  },
  { 
    slug: 'bangalore-chennai', 
    label: 'Bangalore → Chennai',
    originCity: 'Bangalore',
    destinationCity: 'Chennai',
    description: 'Overnight buses available'
  },
  { 
    slug: 'delhi-jaipur', 
    label: 'Delhi → Jaipur',
    originCity: 'Delhi',
    destinationCity: 'Jaipur',
    description: 'Popular weekend getaway route'
  },
  { 
    slug: 'hyderabad-bangalore', 
    label: 'Hyderabad → Bangalore',
    originCity: 'Hyderabad',
    destinationCity: 'Bangalore',
    description: 'Multiple operators, sleeper and seater'
  },
  { 
    slug: 'mumbai-goa', 
    label: 'Mumbai → Goa',
    originCity: 'Mumbai',
    destinationCity: 'Goa',
    description: 'Beach getaway overnight buses'
  },
  { 
    slug: 'chennai-bangalore', 
    label: 'Chennai → Bangalore',
    originCity: 'Chennai',
    destinationCity: 'Bangalore',
    description: 'Frequent services both ways'
  },
]

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * Flight Route Card with Image
 * Uses Next.js Image for lazy loading and optimization
 * 
 * Image path: /images/flights/{route-slug}.webp
 * Alt text: "{Origin} to {Destination} flight route"
 */
function FlightRouteCard({ route }: { route: FlightRouteData }) {
  // Image path: /images/flights/{route-slug}.webp
  // Images are now available in public/images/flights/
  const hasImage = true
  const imageSrc = `/images/flights/${route.slug}.webp`
  
  return (
    <article className="group relative overflow-hidden rounded-xl bg-white shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      {/* Image container with dark gradient overlay for text readability */}
      <div className="relative h-36 overflow-hidden">
        {hasImage ? (
          <>
            <Image
              src={imageSrc}
              alt={`${route.origin} to ${route.destination} flight route`}
              fill
              sizes="(max-width: 768px) 50vw, 300px"
              className="object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            {/* Dark gradient overlay for text readability */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
          </>
        ) : (
          /* Gradient fallback when images not available */
          <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600">
            <span className="absolute inset-0 flex items-center justify-center text-3xl font-bold text-white/30">
              {route.originCode} → {route.destinationCode}
            </span>
            {/* Dark gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          </div>
        )}
        
        {/* Route label - always visible */}
        <div className="absolute bottom-3 left-3 right-3">
          <span className="text-white font-semibold text-lg drop-shadow-md">
            {route.origin} → {route.destination}
          </span>
        </div>
      </div>
      
      {/* CTA - unchanged */}
      <Link 
        href={`/flights/${route.slug}`}
        className="block p-3 text-center text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 transition-colors"
        aria-label={`Search flights from ${route.origin} to ${route.destination}`}
      >
        Search Flights →
      </Link>
    </article>
  )
}

/**
 * Hotel Destination Card with Image
 * 
 * UX PRINCIPLE: Popular cards should provide a frictionless experience.
 * 
 * When user clicks a popular hotel destination:
 * 1. Auto-assign check-in = today + 1, check-out = today + 2
 * 2. Navigate directly to results page with complete params
 * 3. NEVER navigate without dates (breaks the page)
 * 
 * Image path: /images/hotels/{city}.webp
 * Alt text: "Hotels in {City}"
 */
function HotelDestinationCard({ destination }: { destination: HotelDestinationData }) {
  // Image path: /images/hotels/{city}.webp
  const hasImage = true
  const imageSrc = `/images/hotels/${destination.slug}.webp`
  
  // Auto-calculate dates: check-in = tomorrow, check-out = day after
  const getCheckInDate = () => {
    const date = new Date()
    date.setDate(date.getDate() + 1)
    return date.toISOString().split('T')[0]
  }
  
  const getCheckOutDate = () => {
    const date = new Date()
    date.setDate(date.getDate() + 2)
    return date.toISOString().split('T')[0]
  }
  
  // Build complete search URL with all required params
  // MANDATORY: city, check_in, check_out, rooms, adults
  const searchUrl = `/hotels/results?city=${encodeURIComponent(destination.city)}&check_in=${getCheckInDate()}&check_out=${getCheckOutDate()}&rooms=1&room_0_adults=2`
  
  return (
    <article className="group relative overflow-hidden rounded-xl bg-white shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      {/* Image container with dark gradient overlay for text readability */}
      <div className="relative h-36 overflow-hidden">
        {hasImage ? (
          <>
            <Image
              src={imageSrc}
              alt={`Hotels in ${destination.city}`}
              fill
              sizes="(max-width: 768px) 50vw, 300px"
              className="object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            {/* Dark gradient overlay for text readability */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
          </>
        ) : (
          /* Gradient fallback when images not available */
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-400 to-purple-600">
            <span className="absolute inset-0 flex items-center justify-center text-3xl font-bold text-white/30">
              {destination.city}
            </span>
            {/* Dark gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          </div>
        )}
        
        {/* City label - always visible */}
        <div className="absolute bottom-3 left-3 right-3">
          <span className="text-white font-semibold text-lg drop-shadow-md">
            {destination.city}
          </span>
        </div>
      </div>
      
      {/* CTA - Navigate directly to results with complete params */}
      <Link 
        href={searchUrl}
        className="block p-3 text-center text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 transition-colors"
        aria-label={`Search hotels in ${destination.city}`}
      >
        Find Hotels →
      </Link>
    </article>
  )
}

/**
 * Popular Flight Routes Section
 * Displays 6 routes max with images and CTAs
 * 
 * SEO: Uses semantic section/h2/article structure
 */
export function PopularFlightRoutes({ currentRoute }: { currentRoute?: string }) {
  const routes = POPULAR_FLIGHT_ROUTES
    .filter(route => route.slug !== currentRoute)
    .slice(0, 6)

  return (
    <section aria-labelledby="popular-flights-heading">
      <h2 
        id="popular-flights-heading"
        className="text-xl font-semibold text-gray-900 mb-4"
      >
        Popular Flight Routes
      </h2>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {routes.map((route) => (
          <FlightRouteCard key={route.slug} route={route} />
        ))}
      </div>
    </section>
  )
}

/**
 * Popular Hotel Destinations Section
 * Displays 6 destinations max with images and CTAs
 * 
 * SEO: Uses semantic section/h2/article structure
 */
export function PopularHotelDestinations({ currentCity }: { currentCity?: string }) {
  const destinations = POPULAR_HOTEL_DESTINATIONS
    .filter(dest => dest.slug !== currentCity)
    .slice(0, 6)

  return (
    <section aria-labelledby="popular-hotels-heading">
      <h2 
        id="popular-hotels-heading"
        className="text-xl font-semibold text-gray-900 mb-4"
      >
        Popular Hotel Destinations
      </h2>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {destinations.map((destination) => (
          <HotelDestinationCard key={destination.slug} destination={destination} />
        ))}
      </div>
    </section>
  )
}

/**
 * Popular Train Routes Section
 * 
 * NAVIGATION CONTRACT:
 * - Navigate directly to /trains/results
 * - Use STATION CODES or _ALL tokens (backend requirement)
 * - Auto-fill departure_date = tomorrow
 * - passengers = 1
 * 
 * URL FORMAT: /trains/results?origin={STATION_CODE}&destination={STATION_CODE}&departure_date=YYYY-MM-DD&passengers=1
 */
export function PopularTrainRoutes() {
  const routes = POPULAR_TRAIN_ROUTES.slice(0, 6)
  
  // Get tomorrow's date for default departure
  const getTomorrowDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }

  return (
    <section aria-labelledby="popular-trains-heading">
      <h2 
        id="popular-trains-heading"
        className="text-xl font-semibold text-gray-900 mb-4"
      >
        Popular Train Routes
      </h2>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {routes.map((route) => {
          // Build complete URL with all required params
          // CRITICAL: Use station codes/ALL tokens (NOT city names)
          const searchUrl = `/trains/results?origin=${encodeURIComponent(route.origin)}&destination=${encodeURIComponent(route.destination)}&departure_date=${getTomorrowDate()}&passengers=1`
          
          return (
            <Link
              key={route.slug}
              href={searchUrl}
              className="group p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V6M5 12l7-7 7 7" />
                  </svg>
                </div>
                <span className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                  {route.label}
                </span>
              </div>
              <p className="text-sm text-gray-600">{route.description}</p>
            </Link>
          )
        })}
      </div>
    </section>
  )
}

/**
 * Popular Bus Routes Section
 * 
 * NAVIGATION CONTRACT:
 * - Navigate directly to /buses/results
 * - Use CITY NAMES only (no stations, no pickup points)
 * - Auto-fill departure_date = tomorrow
 * - passengers = 1
 * 
 * URL FORMAT: /buses/results?origin={city}&destination={city}&departure_date=YYYY-MM-DD&passengers=1
 */
export function PopularBusRoutes() {
  const routes = POPULAR_BUS_ROUTES.slice(0, 6)
  
  // Get tomorrow's date for default departure
  const getTomorrowDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }

  return (
    <section aria-labelledby="popular-buses-heading">
      <h2 
        id="popular-buses-heading"
        className="text-xl font-semibold text-gray-900 mb-4"
      >
        Popular Bus Routes
      </h2>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {routes.map((route) => {
          // Build complete URL with all required params
          // CRITICAL: Use city names only
          const searchUrl = `/buses/results?origin=${encodeURIComponent(route.originCity)}&destination=${encodeURIComponent(route.destinationCity)}&departure_date=${getTomorrowDate()}&passengers=1`
          
          return (
            <Link
              key={route.slug}
              href={searchUrl}
              className="group p-4 bg-white rounded-xl border border-gray-200 hover:border-orange-300 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                  </svg>
                </div>
                <span className="font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">
                  {route.label}
                </span>
              </div>
              <p className="text-sm text-gray-600">{route.description}</p>
            </Link>
          )
        })}
      </div>
    </section>
  )
}

// ============================================================================
// LEGACY COMPONENTS (Text-only - kept for backward compatibility)
// ============================================================================

interface RouteLink {
  slug: string
  label: string
}

/**
 * @deprecated Use PopularFlightRoutes instead
 * Text-only version for minimal impact sections
 */
export function PopularFlightRoutesText({ currentRoute }: { currentRoute?: string }) {
  const routes: RouteLink[] = POPULAR_FLIGHT_ROUTES.map(r => ({
    slug: r.slug,
    label: r.label
  })).filter(route => route.slug !== currentRoute)

  return (
    <div className="py-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Popular Flight Routes
      </h3>
      <div className="flex flex-wrap gap-3">
        {routes.slice(0, 6).map((route) => (
          <Link
            key={route.slug}
            href={`/flights/${route.slug}`}
            className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm"
          >
            {route.label}
          </Link>
        ))}
      </div>
    </div>
  )
}

/**
 * @deprecated Use PopularHotelDestinations instead
 * Text-only version for minimal impact sections
 */
export function PopularHotelDestinationsText({ currentCity }: { currentCity?: string }) {
  const cities: RouteLink[] = POPULAR_HOTEL_DESTINATIONS.map(d => ({
    slug: d.slug,
    label: d.label
  })).filter(city => city.slug !== currentCity)

  return (
    <div className="py-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Popular Hotel Destinations
      </h3>
      <div className="flex flex-wrap gap-3">
        {cities.slice(0, 5).map((city) => (
          <Link
            key={city.slug}
            href={`/hotels/${city.slug}`}
            className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 transition-colors text-sm"
          >
            {city.label}
          </Link>
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// ADDITIONAL SEO COMPONENTS (unchanged)
// ============================================================================

/**
 * Related Routes Grid
 * Contextual internal links based on origin/destination
 */
export function RelatedRoutesGrid({ 
  origin, 
  destination 
}: { 
  origin: string
  destination: string 
}) {
  const routesFromOrigin: Record<string, RouteLink[]> = {
    DEL: [
      { slug: 'delhi-to-mumbai', label: 'Delhi to Mumbai' },
      { slug: 'delhi-to-goa', label: 'Delhi to Goa' },
      { slug: 'delhi-to-bangalore', label: 'Delhi to Bangalore' },
    ],
    BOM: [
      { slug: 'mumbai-to-delhi', label: 'Mumbai to Delhi' },
      { slug: 'mumbai-to-goa', label: 'Mumbai to Goa' },
      { slug: 'mumbai-to-bangalore', label: 'Mumbai to Bangalore' },
    ],
    BLR: [
      { slug: 'bangalore-to-delhi', label: 'Bangalore to Delhi' },
      { slug: 'bangalore-to-mumbai', label: 'Bangalore to Mumbai' },
    ],
  }

  const relatedRoutes = routesFromOrigin[origin] || []

  if (relatedRoutes.length === 0) return null

  return (
    <div className="py-6 border-t border-gray-200">
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        More flights from {origin}
      </h4>
      <div className="flex flex-wrap gap-2">
        {relatedRoutes.map((route) => (
          <Link
            key={route.slug}
            href={`/flights/${route.slug}`}
            className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm"
          >
            {route.label}
          </Link>
        ))}
      </div>
    </div>
  )
}

/**
 * Hotel CTA for Flight Pages
 */
export function HotelCTAForDestination({ 
  destinationCity, 
  destinationCode 
}: { 
  destinationCity: string
  destinationCode: string 
}) {
  const citySlugMap: Record<string, string> = {
    BOM: 'mumbai',
    DEL: 'delhi',
    BLR: 'bangalore',
    GOI: 'goa',
    HYD: 'hyderabad',
    MAA: 'chennai',
    CCU: 'kolkata',
    PNQ: 'pune',
    JAI: 'jaipur',
    COK: 'kochi',
  }

  const citySlug = citySlugMap[destinationCode]
  if (!citySlug) return null

  return (
    <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
      <p className="text-sm text-gray-700 mb-2">
        Planning to stay in {destinationCity}?
      </p>
      <Link
        href={`/hotels/${citySlug}`}
        className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
      >
        Compare hotels in {destinationCity} →
      </Link>
    </div>
  )
}
