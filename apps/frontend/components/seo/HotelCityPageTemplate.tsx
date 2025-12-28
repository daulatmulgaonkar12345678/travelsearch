/**
 * SEO Hotel City Page Template
 * 
 * Reusable template for static SEO-friendly hotel city pages.
 * Each page includes:
 * - SEO-optimized H1 and meta tags
 * - Informative content about the destination
 * - Clear affiliate disclosure
 * - CTA button to live search results
 */

import { Metadata } from 'next'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'

export interface HotelCityPageProps {
  cityName: string
  cityCode: string
  content: {
    title: string
    description: string
    whyVisit: string
    accommodation: string
    bookingInfo: string
  }
  relatedCities: Array<{
    slug: string
    label: string
  }>
  nearbyFlightRoutes?: Array<{
    slug: string
    label: string
  }>
}

/**
 * Generate metadata for SEO hotel city pages
 */
export function generateHotelCityMetadata(props: HotelCityPageProps): Metadata {
  const { cityName, content } = props
  
  return {
    title: `Hotels in ${cityName} | Compare Accommodation | TravelSearch`,
    description: `Compare hotel prices in ${cityName}. ${content.description} Find accommodation from budget to luxury options.`,
    robots: {
      index: true,
      follow: true,
    },
    openGraph: {
      title: `Hotels in ${cityName}`,
      description: `Compare hotel prices in ${cityName}. Find the right accommodation for your trip.`,
      type: 'website',
    },
  }
}

/**
 * Get default check-in/check-out dates
 */
function getDefaultDates(): { checkIn: string; checkOut: string } {
  const checkIn = new Date()
  checkIn.setDate(checkIn.getDate() + 14)
  const checkOut = new Date(checkIn)
  checkOut.setDate(checkOut.getDate() + 2)
  
  return {
    checkIn: checkIn.toISOString().split('T')[0],
    checkOut: checkOut.toISOString().split('T')[0],
  }
}

export default function HotelCityPageTemplate({
  cityName,
  cityCode,
  content,
  relatedCities,
  nearbyFlightRoutes = [],
}: HotelCityPageProps) {
  // UX PRINCIPLE: Prefill, don't auto-search
  // Instead of navigating directly to results (which caused "Missing parameters" errors),
  // navigate to homepage with prefill param so user can select dates
  const prefillUrl = `/?tab=hotels&prefill_city=${encodeURIComponent(cityName)}`

  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-indigo-50 to-purple-50 py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              {content.title}
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              {content.description}
            </p>
            <Link
              href={searchUrl}
              className="inline-flex items-center px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Search Hotels in {cityName}
            </Link>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Why Visit */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Why Visit {cityName}
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.whyVisit}
            </p>
          </div>

          {/* Accommodation */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Accommodation Options
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.accommodation}
            </p>
          </div>

          {/* Booking Info */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              How to Book
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.bookingInfo}
            </p>
          </div>

          {/* CTA Box */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 mb-10">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Find your stay in {cityName}
            </h3>
            <p className="text-gray-600 mb-4">
              Hotel availability and prices are provided by third-party partners. Compare options across multiple booking platforms.
            </p>
            <Link
              href={searchUrl}
              className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Compare Hotel Prices
            </Link>
          </div>

          {/* Flight Routes to this City */}
          {nearbyFlightRoutes.length > 0 && (
            <div className="mb-8 p-6 bg-blue-50 rounded-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Flights to {cityName}
              </h3>
              <div className="flex flex-wrap gap-3">
                {nearbyFlightRoutes.map((route) => (
                  <Link
                    key={route.slug}
                    href={`/flights/${route.slug}`}
                    className="px-4 py-2 bg-white text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm border border-blue-200"
                  >
                    {route.label}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Related Cities */}
          {relatedCities.length > 0 && (
            <div className="border-t border-gray-200 pt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Explore Other Destinations
              </h3>
              <div className="flex flex-wrap gap-3">
                {relatedCities.map((city) => (
                  <Link
                    key={city.slug}
                    href={`/hotels/${city.slug}`}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    {city.label}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Compliance Notice */}
      <section className="bg-gray-50 border-t border-gray-200 py-6">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs text-gray-500">
              Hotel availability and prices are provided by our travel partners and may change. 
              TravelSearch is a metasearch engine - you'll complete your booking directly on the provider's website.
              We may earn a commission when you book through our links.
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
