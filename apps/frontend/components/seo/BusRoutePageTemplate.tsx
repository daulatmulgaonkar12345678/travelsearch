/**
 * SEO Bus Route Page Template
 * 
 * Server-rendered template for bus route SEO pages.
 * Features:
 * - SEO-optimized H1 and meta tags
 * - JSON-LD schema markup (Product, Breadcrumb, FAQ)
 * - Estimated price range
 * - FAQ section for rich snippets
 * - Internal links for topical authority
 * - No JS required for content rendering
 */

import { Metadata } from 'next'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import BusRouteSchema from './schema/BusRouteSchema'

export interface BusRoutePageProps {
  originCity: string
  destinationCity: string
  content: {
    title: string
    description: string
    routeInfo: string
    busTypes: string
    travelTips: string
  }
  estimatedPrice?: {
    min: number
    max: number
    currency: string
  }
  duration?: string
  faqs?: Array<{
    question: string
    answer: string
  }>
  relatedRoutes: Array<{
    slug: string
    label: string
  }>
}

/**
 * Generate metadata for SEO bus route pages (Server-side)
 */
export function generateBusRouteMetadata(props: BusRoutePageProps): Metadata {
  const { originCity, destinationCity, content, estimatedPrice } = props
  
  // Title ≤ 60 chars
  const title = `${originCity} to ${destinationCity} Bus | Book Tickets Online`
  
  // Description ≤ 155 chars
  const description = `Book ${originCity} to ${destinationCity} bus tickets. ${estimatedPrice ? `Fares from ₹${estimatedPrice.min}.` : ''} Compare AC, sleeper & seater buses across operators.`
  
  return {
    title: title.slice(0, 60),
    description: description.slice(0, 155),
    robots: {
      index: true,
      follow: true,
    },
    openGraph: {
      title: `${originCity} to ${destinationCity} Bus`,
      description: `Compare bus ticket prices from ${originCity} to ${destinationCity}.`,
      type: 'website',
    },
  }
}

/**
 * Default FAQs generator for bus routes
 */
function getDefaultFAQs(originCity: string, destinationCity: string, estimatedPrice?: { min: number; max: number; currency: string }, duration?: string): Array<{ question: string; answer: string }> {
  return [
    {
      question: `How much does a bus ticket from ${originCity} to ${destinationCity} cost?`,
      answer: `Bus ticket prices from ${originCity} to ${destinationCity} typically range from ${estimatedPrice ? `₹${estimatedPrice.min} to ₹${estimatedPrice.max}` : '₹300 to ₹2,500'} depending on the bus type (AC, Non-AC, Sleeper, Seater) and operator.`,
    },
    {
      question: `How long does the bus journey from ${originCity} to ${destinationCity} take?`,
      answer: `The bus journey from ${originCity} to ${destinationCity} typically takes ${duration || '4-8 hours'} depending on traffic conditions, bus type, and route taken.`,
    },
    {
      question: `What types of buses run between ${originCity} and ${destinationCity}?`,
      answer: `Various bus types operate on the ${originCity} to ${destinationCity} route including AC sleeper, Non-AC sleeper, AC seater, and ordinary buses. Compare options to find what suits your comfort and budget.`,
    },
  ]
}

export default function BusRoutePageTemplate({
  originCity,
  destinationCity,
  content,
  estimatedPrice = { min: 300, max: 2500, currency: 'INR' },
  duration = '4-8 hours',
  faqs,
  relatedRoutes,
}: BusRoutePageProps) {
  // Use provided FAQs or generate defaults
  const displayFAQs = faqs || getDefaultFAQs(originCity, destinationCity, estimatedPrice, duration)
  
  // CTA URL
  const searchUrl = `/?tab=buses&from=${encodeURIComponent(originCity)}&to=${encodeURIComponent(destinationCity)}`

  return (
    <div className="min-h-screen bg-white">
      {/* JSON-LD Schema Markup (Server-rendered) */}
      <BusRouteSchema
        originCity={originCity}
        destinationCity={destinationCity}
        estimatedPrice={estimatedPrice}
        duration={duration}
        faqs={displayFAQs}
      />
      
      <Navigation />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-orange-50 to-red-50 py-12 md:py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            {/* H1 - Only one per page */}
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              {originCity} to {destinationCity} Bus Tickets
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
              {content.description}
            </p>
            
            {/* Price & Duration Indicators */}
            <div className="flex justify-center gap-4 flex-wrap mb-8">
              <div className="bg-white rounded-xl px-6 py-4 shadow-sm border border-gray-100">
                <p className="text-sm text-gray-500 mb-1">Estimated Fare</p>
                <p className="text-2xl font-bold text-green-600">
                  ₹{estimatedPrice.min} – ₹{estimatedPrice.max}
                </p>
              </div>
              <div className="bg-white rounded-xl px-6 py-4 shadow-sm border border-gray-100">
                <p className="text-sm text-gray-500 mb-1">Journey Time</p>
                <p className="text-2xl font-bold text-blue-600">
                  {duration}
                </p>
              </div>
            </div>
            
            {/* CTA Button */}
            <Link
              href={searchUrl}
              className="inline-flex items-center px-8 py-4 bg-orange-600 text-white font-semibold rounded-xl hover:bg-orange-700 transition-colors"
            >
              Search Bus Tickets
            </Link>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Route Information */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Route Information
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.routeInfo}
            </p>
          </div>

          {/* Bus Types */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Bus Types Available
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.busTypes}
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

          {/* FAQ Section */}
          <div className="mb-10 bg-gray-50 rounded-xl p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">
              Frequently Asked Questions
            </h2>
            <div className="space-y-6">
              {displayFAQs.map((faq, index) => (
                <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
                  <h3 className="font-medium text-gray-900 mb-2">
                    {faq.question}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {faq.answer}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Related Routes (Internal Links) */}
          {relatedRoutes.length > 0 && (
            <div className="border-t border-gray-200 pt-8 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Popular Bus Routes
              </h3>
              <div className="flex flex-wrap gap-3">
                {relatedRoutes.map((route) => (
                  <Link
                    key={route.slug}
                    href={`/buses/${route.slug}`}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    {route.label} →
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* CTA Box */}
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Book Your Bus Ticket
            </h3>
            <p className="text-gray-600 mb-4">
              Compare prices across multiple bus operators and book your {originCity} to {destinationCity} bus ticket.
            </p>
            <Link
              href={searchUrl}
              className="inline-flex items-center px-6 py-3 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
            >
              Compare Bus Tickets
            </Link>
          </div>
        </div>
      </section>

      {/* Compliance Notice */}
      <section className="bg-gray-50 border-t border-gray-200 py-6">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs text-gray-500">
              Bus fares and schedules are estimates provided by our travel partners and may vary. 
              TravelSearch is a metasearch engine - you'll complete your booking directly on the operator's website.
              We may earn a commission when you book through our links.
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
