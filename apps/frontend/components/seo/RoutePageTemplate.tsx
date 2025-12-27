/**
 * SEO Route Page Template
 * 
 * Reusable template for static SEO-friendly flight route pages.
 * Each page includes:
 * - SEO-optimized H1 and meta tags
 * - Helpful, unique content (150-300 words)
 * - Embedded search bar with pre-filled route (UX improvement)
 * - Internal links to related routes
 * 
 * UX PRINCIPLE: User clicks route → everything auto-filled → adjust date → search
 */

import { Metadata } from 'next'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import RouteSearchBar from './RouteSearchBar'

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
      description: `Compare flight prices from ${originCity} to ${destinationCity}. Search multiple providers instantly.`,
      type: 'website',
    },
  }
}

export default function RoutePageTemplate({
  originCity,
  originCode,
  destinationCity,
  destinationCode,
  content,
  relatedRoutes,
}: RoutePageProps) {
  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      {/* Hero Section with Embedded Search */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-12 md:py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            {/* Title */}
            <div className="text-center mb-8">
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
                {content.title}
              </h1>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                {content.description}
              </p>
            </div>

            {/* Embedded Search Bar - Client Component */}
            <div className="max-w-xl mx-auto">
              <RouteSearchBar
                originCode={originCode}
                originCity={originCity}
                destinationCode={destinationCode}
                destinationCity={destinationCity}
              />
            </div>
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
