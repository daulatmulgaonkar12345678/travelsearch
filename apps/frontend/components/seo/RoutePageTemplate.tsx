/**
 * SEO Route Page Template (Enhanced)
 * 
 * Server-rendered template for flight route SEO pages.
 * Features:
 * - SEO-optimized H1 and meta tags
 * - JSON-LD schema markup (Product, Breadcrumb, FAQ)
 * - Estimated price range (clearly labeled)
 * - FAQ section for rich snippets
 * - Internal links for topical authority
 * - No JS required for content rendering
 */

import { Metadata } from 'next'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import RouteSearchBar from './RouteSearchBar'
import FlightRouteSchema from './schema/FlightRouteSchema'

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
  estimatedPrice?: {
    min: number
    max: number
    currency: string
  }
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
 * Generate metadata for SEO route pages (Server-side)
 */
export function generateRouteMetadata(props: RoutePageProps): Metadata {
  const { originCity, destinationCity, content, estimatedPrice } = props
  
  // Title ≤ 60 chars
  const title = `Cheap Flights ${originCity} to ${destinationCity} | Compare Prices`
  
  // Description ≤ 155 chars
  const description = `Compare ${originCity} to ${destinationCity} flight options across trusted booking partners. ${estimatedPrice ? `Fares from ₹${estimatedPrice.min.toLocaleString()}.` : ''} Book on official sites.`
  
  return {
    title: title.slice(0, 60),
    description: description.slice(0, 155),
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

/**
 * Default FAQs generator for flight routes
 */
function getDefaultFAQs(originCity: string, destinationCity: string, estimatedPrice?: { min: number; max: number; currency: string }): Array<{ question: string; answer: string }> {
  return [
    {
      question: `How much do flights from ${originCity} to ${destinationCity} cost?`,
      answer: `Flight prices from ${originCity} to ${destinationCity} typically range from ${estimatedPrice ? `₹${estimatedPrice.min.toLocaleString()} to ₹${estimatedPrice.max.toLocaleString()}` : '₹3,000 to ₹15,000'} depending on the airline, booking time, and travel dates. Prices are estimates and may vary.`,
    },
    {
      question: `What is the best time to book ${originCity} to ${destinationCity} flights?`,
      answer: `For the best fares on ${originCity} to ${destinationCity} flights, consider booking 2-3 weeks in advance for domestic routes. Weekday flights typically offer better prices than weekend departures.`,
    },
    {
      question: `How long is the flight from ${originCity} to ${destinationCity}?`,
      answer: `Flight duration from ${originCity} to ${destinationCity} varies by airline and routing. Direct flights are typically faster, while connecting flights may take longer but sometimes offer lower fares.`,
    },
  ]
}

export default function RoutePageTemplate({
  originCity,
  originCode,
  destinationCity,
  destinationCode,
  content,
  estimatedPrice = { min: 3000, max: 15000, currency: 'INR' },
  faqs,
  relatedRoutes,
}: RoutePageProps) {
  // Use provided FAQs or generate defaults
  const displayFAQs = faqs || getDefaultFAQs(originCity, destinationCity, estimatedPrice)
  
  return (
    <div className="min-h-screen bg-white">
      {/* JSON-LD Schema Markup (Server-rendered) */}
      <FlightRouteSchema
        originCity={originCity}
        originCode={originCode}
        destinationCity={destinationCity}
        destinationCode={destinationCode}
        estimatedPrice={estimatedPrice}
        faqs={displayFAQs}
      />
      
      <Navigation />

      {/* Hero Section with Embedded Search */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-12 md:py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            {/* H1 - Only one per page, renders without JS */}
            <div className="text-center mb-8">
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
                Cheap Flights from {originCity} to {destinationCity}
              </h1>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                {content.description}
              </p>
            </div>

            {/* Price Range Indicator (Clearly labeled as estimate) */}
            <div className="flex justify-center mb-8">
              <div className="bg-white rounded-xl px-6 py-4 shadow-sm border border-gray-100">
                <div className="text-center">
                  <p className="text-sm text-gray-500 mb-1">Estimated Price Range</p>
                  <p className="text-2xl font-bold text-green-600">
                    ₹{estimatedPrice.min.toLocaleString()} – ₹{estimatedPrice.max.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Prices vary by date and availability</p>
                </div>
              </div>
            </div>

            {/* Embedded Search Bar - CTA to search flow */}
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

      {/* Main Content - 150-300 words, renders without JS */}
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

          {/* FAQ Section (For Rich Snippets) */}
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

          {/* Internal Links - Related Routes */}
          {relatedRoutes.length > 0 && (
            <div className="border-t border-gray-200 pt-8 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Popular Routes
              </h3>
              <div className="flex flex-wrap gap-3">
                {relatedRoutes.map((route) => (
                  <Link
                    key={route.slug}
                    href={`/flights/${route.slug}`}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    {route.label} →
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* CTA Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ready to Compare Prices?
            </h3>
            <p className="text-gray-600 mb-4">
              Search across multiple airlines and booking sites to find the best {originCity} to {destinationCity} flight for your trip.
            </p>
            <Link
              href={`/?tab=flights&from=${originCode}&to=${destinationCode}`}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Search Flights
            </Link>
          </div>
        </div>
      </section>

      {/* Compliance Notice */}
      <section className="bg-gray-50 border-t border-gray-200 py-6">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs text-gray-500">
              Prices displayed are estimates provided by our travel partners and may vary. 
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
