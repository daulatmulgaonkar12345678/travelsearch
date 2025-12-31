/**
 * SEO Hotel City Page Template (Enhanced)
 * 
 * Server-rendered template for hotel city SEO pages.
 * Features:
 * - SEO-optimized H1 and meta tags
 * - JSON-LD schema markup (Hotel, Breadcrumb, FAQ)
 * - Estimated price range
 * - FAQ section for rich snippets
 * - Internal links to areas and flight routes
 * - No JS required for content rendering
 */

import { Metadata } from 'next'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import HotelCitySchema from './schema/HotelCitySchema'

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
  estimatedPrice?: {
    min: number
    max: number
    currency: string
  }
  faqs?: Array<{
    question: string
    answer: string
  }>
  popularAreas?: Array<{
    slug: string
    label: string
  }>
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
 * Generate metadata for SEO hotel city pages (Server-side)
 */
export function generateHotelCityMetadata(props: HotelCityPageProps): Metadata {
  const { cityName, content, estimatedPrice } = props
  
  // Title ≤ 60 chars
  const title = `Hotels in ${cityName} | Compare Prices & Book`
  
  // Description ≤ 155 chars
  const description = `Compare hotel prices in ${cityName}. ${estimatedPrice ? `From ₹${estimatedPrice.min.toLocaleString()}/night.` : ''} ${content.description.slice(0, 80)}`
  
  return {
    title: title.slice(0, 60),
    description: description.slice(0, 155),
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
 * Default FAQs generator for hotel cities
 */
function getDefaultFAQs(cityName: string, estimatedPrice?: { min: number; max: number; currency: string }): Array<{ question: string; answer: string }> {
  return [
    {
      question: `What is the average hotel price in ${cityName}?`,
      answer: `Hotel prices in ${cityName} typically range from ${estimatedPrice ? `₹${estimatedPrice.min.toLocaleString()} to ₹${estimatedPrice.max.toLocaleString()}` : '₹1,500 to ₹25,000'} per night depending on the hotel category, location, and season. Budget options start lower, while luxury properties cost more.`,
    },
    {
      question: `What are the best areas to stay in ${cityName}?`,
      answer: `The best area to stay in ${cityName} depends on your travel purpose. Business travelers often prefer central locations, while tourists may prefer areas near attractions. Compare options across different neighborhoods to find what suits your needs.`,
    },
    {
      question: `How do I find cheap hotels in ${cityName}?`,
      answer: `To find affordable hotels in ${cityName}, compare prices across multiple booking platforms, be flexible with dates, and book in advance. TravelSearch helps you compare prices from various sites to find the best deal.`,
    },
  ]
}

export default function HotelCityPageTemplate({
  cityName,
  cityCode,
  content,
  estimatedPrice = { min: 1500, max: 25000, currency: 'INR' },
  faqs,
  popularAreas = [],
  relatedCities,
  nearbyFlightRoutes = [],
}: HotelCityPageProps) {
  // Use provided FAQs or generate defaults
  const displayFAQs = faqs || getDefaultFAQs(cityName, estimatedPrice)
  
  // CTA URL - prefill form instead of direct navigation
  const prefillUrl = `/?tab=hotels&prefill_city=${encodeURIComponent(cityName)}`

  return (
    <div className="min-h-screen bg-white">
      {/* JSON-LD Schema Markup (Server-rendered) */}
      <HotelCitySchema
        cityName={cityName}
        cityCode={cityCode}
        estimatedPrice={estimatedPrice}
        faqs={displayFAQs}
      />
      
      <Navigation />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-indigo-50 to-purple-50 py-12 md:py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            {/* H1 - Only one per page, renders without JS */}
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Hotels in {cityName}
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              {content.description}
            </p>
            
            {/* Price Range Indicator */}
            <div className="inline-block bg-white rounded-xl px-6 py-4 shadow-sm border border-gray-100 mb-8">
              <p className="text-sm text-gray-500 mb-1">Estimated Price Range</p>
              <p className="text-2xl font-bold text-green-600">
                ₹{estimatedPrice.min.toLocaleString()} – ₹{estimatedPrice.max.toLocaleString()}
                <span className="text-base font-normal text-gray-500">/night</span>
              </p>
            </div>
            
            {/* CTA Button */}
            <div>
              <Link
                href={prefillUrl}
                className="inline-flex items-center px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
              >
                Search Hotels in {cityName}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content - 150-300 words, renders without JS */}
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

          {/* Popular Areas (Internal Links) */}
          {popularAreas.length > 0 && (
            <div className="mb-8 p-6 bg-purple-50 rounded-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Popular Areas in {cityName}
              </h3>
              <div className="flex flex-wrap gap-3">
                {popularAreas.map((area) => (
                  <Link
                    key={area.slug}
                    href={`/hotels/${cityName.toLowerCase()}/${area.slug}`}
                    className="px-4 py-2 bg-white text-purple-700 rounded-lg hover:bg-purple-100 transition-colors text-sm border border-purple-200"
                  >
                    Hotels in {area.label} →
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Flight Routes to this City (Cross-service links) */}
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
                    {route.label} →
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Related Cities (Internal Links) */}
          {relatedCities.length > 0 && (
            <div className="border-t border-gray-200 pt-8 mb-8">
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
                    {city.label} →
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* CTA Box */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Find Your Stay in {cityName}
            </h3>
            <p className="text-gray-600 mb-4">
              Compare hotel options across multiple booking platforms to find the best accommodation for your trip.
            </p>
            <Link
              href={prefillUrl}
              className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Compare Hotel Prices
            </Link>
          </div>
        </div>
      </section>

      {/* Compliance Notice */}
      <section className="bg-gray-50 border-t border-gray-200 py-6">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs text-gray-500">
              Hotel availability and prices are estimates provided by our travel partners and may change. 
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
