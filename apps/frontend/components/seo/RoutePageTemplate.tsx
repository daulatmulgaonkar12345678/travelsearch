/**
 * SEO Route Page Template
 * 
 * Reusable template for static SEO-friendly flight route pages.
 * Each page includes:
 * - SEO-optimized H1 and meta tags
 * - Helpful, unique content (150-300 words)
 * - Internal links to related routes
 * - CTA button to live search results
 */

import { Metadata } from 'next'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'

export interface RoutePageProps {
  originCity: string
  originCode: string
  destinationCity: string
  destinationCode: string
  content: {
    title: string
    description: string
    flightInfo: string
    travelTips: string
    bestTime: string
  }
  relatedRoutes: Array<{
    slug: string
    label: string
  }>
}

/**
 * Generate metadata for SEO route pages
 */
export function generateRouteMetadata(props: RoutePageProps): Metadata {
  const { originCity, destinationCity, content } = props
  
  return {
    title: `${originCity} to ${destinationCity} Flights | Compare Cheap Fares | TravelSearch`,
    description: `Find cheap flights from ${originCity} to ${destinationCity}. Compare prices across multiple airlines and booking sites. ${content.description}`,
    robots: {
      index: true,
      follow: true,
    },
    openGraph: {
      title: `${originCity} to ${destinationCity} Flights`,
      description: `Compare flight prices from ${originCity} to ${destinationCity}. Find the best deals instantly.`,
      type: 'website',
    },
  }
}

/**
 * Get today's date in YYYY-MM-DD format for search URL
 */
function getDefaultSearchDate(): string {
  const date = new Date()
  date.setDate(date.getDate() + 14) // Default to 2 weeks from now
  return date.toISOString().split('T')[0]
}

export default function RoutePageTemplate({
  originCity,
  originCode,
  destinationCity,
  destinationCode,
  content,
  relatedRoutes,
}: RoutePageProps) {
  const searchUrl = `/flights/results?origin=${originCode}&destination=${destinationCode}&departure_date=${getDefaultSearchDate()}&trip_type=oneway&adults=1&cabin_class=economy`

  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-16">
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
              className="inline-flex items-center px-8 py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors"
            >
              Search {originCity} to {destinationCity} Flights
            </Link>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Flight Information */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Flight Information
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.flightInfo}
            </p>
          </div>

          {/* Travel Tips */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Travel Tips
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.travelTips}
            </p>
          </div>

          {/* Best Time to Book */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Best Time to Book
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.bestTime}
            </p>
          </div>

          {/* CTA Box */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 mb-10">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ready to book your {originCity} to {destinationCity} flight?
            </h3>
            <p className="text-gray-600 mb-4">
              Compare prices across multiple airlines and booking sites. Prices shown are sourced from our travel partners.
            </p>
            <Link
              href={searchUrl}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Compare Flight Prices
            </Link>
          </div>

          {/* Related Routes */}
          {relatedRoutes.length > 0 && (
            <div className="border-t border-gray-200 pt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Explore More Routes
              </h3>
              <div className="flex flex-wrap gap-3">
                {relatedRoutes.map((route) => (
                  <Link
                    key={route.slug}
                    href={`/flights/${route.slug}`}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    {route.label}
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
              Prices displayed are provided by our travel partners and may vary. 
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
