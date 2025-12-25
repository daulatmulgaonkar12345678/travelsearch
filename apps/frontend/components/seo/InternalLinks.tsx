/**
 * Internal Linking Components for SEO
 * 
 * Reusable components for cross-linking between pages.
 * Improves crawlability and SEO without footer spam.
 */

import Link from 'next/link'

interface RouteLink {
  slug: string
  label: string
}

/**
 * Popular Routes Section
 * Use on homepage or destination pages to link to top flight routes
 */
export function PopularFlightRoutes({ currentRoute }: { currentRoute?: string }) {
  const routes: RouteLink[] = [
    { slug: 'delhi-to-mumbai', label: 'Delhi to Mumbai' },
    { slug: 'mumbai-to-bangalore', label: 'Mumbai to Bangalore' },
    { slug: 'delhi-to-goa', label: 'Delhi to Goa' },
    { slug: 'bangalore-to-delhi', label: 'Bangalore to Delhi' },
    { slug: 'mumbai-to-goa', label: 'Mumbai to Goa' },
    { slug: 'hyderabad-to-bangalore', label: 'Hyderabad to Bangalore' },
    { slug: 'chennai-to-delhi', label: 'Chennai to Delhi' },
    { slug: 'kolkata-to-delhi', label: 'Kolkata to Delhi' },
  ].filter(route => route.slug !== currentRoute)

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
 * Popular Hotel Destinations
 * Use on homepage or flight pages to cross-link to hotel pages
 */
export function PopularHotelDestinations({ currentCity }: { currentCity?: string }) {
  const cities: RouteLink[] = [
    { slug: 'mumbai', label: 'Hotels in Mumbai' },
    { slug: 'delhi', label: 'Hotels in Delhi' },
    { slug: 'bangalore', label: 'Hotels in Bangalore' },
    { slug: 'goa', label: 'Hotels in Goa' },
    { slug: 'jaipur', label: 'Hotels in Jaipur' },
    { slug: 'chennai', label: 'Hotels in Chennai' },
  ].filter(city => city.slug !== currentCity)

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
  // Routes from same origin
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
 * Cross-link from flight route pages to hotel pages
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
