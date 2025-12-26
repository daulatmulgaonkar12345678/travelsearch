/**
 * Internal Linking Components for SEO - Enhanced with Images
 * 
 * Features:
 * - Static destination images (WebP preferred)
 * - Lazy loading for performance (LCP-friendly)
 * - Semantic HTML (section, h2, article)
 * - Proper alt text for accessibility/SEO
 * - Graceful fallback if images missing
 * - Limited to 6-8 items for performance
 * 
 * Image Storage:
 * - Images stored in /public/images/destinations/ and /public/images/routes/
 * - Naming convention: {city-slug}.webp (e.g., mumbai.webp, delhi-to-mumbai.webp)
 * - Recommended size: 400x300px for cards
 * 
 * SEO Notes:
 * - Alt text includes route/destination name
 * - Internal links boost crawlability
 * - Schema markup can be added later for richer results
 */

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

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * Flight Route Card with Image
 * Uses Next.js Image for lazy loading and optimization
 */
function FlightRouteCard({ route }: { route: FlightRouteData }) {
  // For now, we use gradient fallback since images aren't uploaded yet
  // Once WebP images are added to /public/images/routes/, set hasImage to true
  const hasImage = false // Set to true when images are available
  const imageSrc = route.image 
    ? `/images/routes/${route.image}`
    : null
  
  return (
    <article className="group relative overflow-hidden rounded-xl bg-white shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      {/* Image with lazy loading */}
      <div className="relative h-36 bg-gradient-to-br from-blue-100 to-blue-200 overflow-hidden">
        {hasImage && imageSrc ? (
          <Image
            src={imageSrc}
            alt={`Flights from ${route.origin} to ${route.destination}`}
            fill
            sizes="(max-width: 768px) 100vw, 300px"
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          /* Fallback gradient with route codes */
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-400 to-blue-600">
            <span className="text-3xl font-bold text-white/30">
              {route.originCode} → {route.destinationCode}
            </span>
          </div>
        )}
        
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
        
        {/* Route badge */}
        <div className="absolute bottom-3 left-3 right-3">
          <span className="text-white font-semibold text-lg drop-shadow-md">
            {route.origin} → {route.destination}
          </span>
        </div>
      </div>
      
      {/* CTA */}
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
 */
function HotelDestinationCard({ destination }: { destination: HotelDestinationData }) {
  // For now, we use gradient fallback since images aren't uploaded yet
  // Once WebP images are added to /public/images/destinations/, set hasImage to true
  const hasImage = false // Set to true when images are available
  const imageSrc = destination.image 
    ? `/images/destinations/${destination.image}`
    : null
  
  return (
    <article className="group relative overflow-hidden rounded-xl bg-white shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      {/* Image with lazy loading */}
      <div className="relative h-36 bg-gradient-to-br from-indigo-100 to-indigo-200 overflow-hidden">
        {hasImage && imageSrc ? (
          <Image
            src={imageSrc}
            alt={`Hotels in ${destination.city}`}
            fill
            sizes="(max-width: 768px) 100vw, 300px"
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          /* Fallback with city name */
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-indigo-400 to-purple-600">
            <span className="text-3xl font-bold text-white/30">
              {destination.city}
            </span>
          </div>
        )}
        
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
        
        {/* City name badge */}
        <div className="absolute bottom-3 left-3 right-3">
          <span className="text-white font-semibold text-lg drop-shadow-md">
            {destination.city}
          </span>
        </div>
      </div>
      
      {/* CTA */}
      <Link 
        href={`/hotels/${destination.slug}`}
        className="block p-3 text-center text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 transition-colors"
        aria-label={`Find hotels in ${destination.city}`}
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
