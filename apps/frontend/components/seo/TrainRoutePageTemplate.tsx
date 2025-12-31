/**
 * SEO Train Route Page Template
 * 
 * Server-rendered template for train route SEO pages.
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
import TrainRouteSchema from './schema/TrainRouteSchema'

export interface TrainRoutePageProps {
  originCity: string
  originStation?: string
  destinationCity: string
  destinationStation?: string
  content: {
    title: string
    description: string
    routeInfo: string
    trainClasses: string
    bookingTips: string
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
 * Generate metadata for SEO train route pages (Server-side)
 */
export function generateTrainRouteMetadata(props: TrainRoutePageProps): Metadata {
  const { originCity, destinationCity, content, estimatedPrice } = props
  
  // Title ≤ 60 chars
  const title = `${originCity} to ${destinationCity} Trains | Check Schedule`
  
  // Description ≤ 155 chars  
  const description = `${originCity} to ${destinationCity} train tickets. ${estimatedPrice ? `From ₹${estimatedPrice.min}.` : ''} Compare Sleeper, AC & General class across booking sites.`
  
  return {
    title: title.slice(0, 60),
    description: description.slice(0, 155),
    robots: {
      index: true,
      follow: true,
    },
    openGraph: {
      title: `${originCity} to ${destinationCity} Trains`,
      description: `Compare train ticket prices from ${originCity} to ${destinationCity}.`,
      type: 'website',
    },
  }
}

/**
 * Default FAQs generator for train routes
 */
function getDefaultFAQs(originCity: string, destinationCity: string, estimatedPrice?: { min: number; max: number; currency: string }, duration?: string): Array<{ question: string; answer: string }> {
  return [
    {
      question: `How much does a train ticket from ${originCity} to ${destinationCity} cost?`,
      answer: `Train ticket prices from ${originCity} to ${destinationCity} range from ${estimatedPrice ? `₹${estimatedPrice.min} to ₹${estimatedPrice.max}` : '₹200 to ₹4,000'} depending on the class (General, Sleeper, AC 3-tier, AC 2-tier, AC 1st class) and train type.`,
    },
    {
      question: `How long does the train journey from ${originCity} to ${destinationCity} take?`,
      answer: `Train journey time from ${originCity} to ${destinationCity} is typically ${duration || '6-12 hours'} depending on the train type. Superfast and Rajdhani trains are faster than express and passenger trains.`,
    },
    {
      question: `How to book ${originCity} to ${destinationCity} train tickets?`,
      answer: `You can book ${originCity} to ${destinationCity} train tickets through IRCTC or authorized booking partners. Compare prices and availability across platforms using TravelSearch before booking.`,
    },
  ]
}

export default function TrainRoutePageTemplate({
  originCity,
  originStation,
  destinationCity,
  destinationStation,
  content,
  estimatedPrice = { min: 200, max: 4000, currency: 'INR' },
  duration = '6-12 hours',
  faqs,
  relatedRoutes,
}: TrainRoutePageProps) {
  // Use provided FAQs or generate defaults
  const displayFAQs = faqs || getDefaultFAQs(originCity, destinationCity, estimatedPrice, duration)
  
  // CTA URL
  const searchUrl = `/?tab=trains&from=${encodeURIComponent(originCity)}&to=${encodeURIComponent(destinationCity)}`

  return (
    <div className="min-h-screen bg-white">
      {/* JSON-LD Schema Markup (Server-rendered) */}
      <TrainRouteSchema
        originCity={originCity}
        originStation={originStation}
        destinationCity={destinationCity}
        destinationStation={destinationStation}
        estimatedPrice={estimatedPrice}
        faqs={displayFAQs}
      />
      
      <Navigation />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-green-50 to-teal-50 py-12 md:py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            {/* H1 - Only one per page */}
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              {originCity} to {destinationCity} Trains
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
                <p className="text-2xl font-bold text-teal-600">
                  {duration}
                </p>
              </div>
            </div>
            
            {/* CTA Button */}
            <Link
              href={searchUrl}
              className="inline-flex items-center px-8 py-4 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
            >
              Search Train Tickets
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

          {/* Train Classes */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Available Classes
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.trainClasses}
            </p>
          </div>

          {/* Booking Tips */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Booking Tips
            </h2>
            <p className="text-gray-700 leading-relaxed">
              {content.bookingTips}
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
                Popular Train Routes
              </h3>
              <div className="flex flex-wrap gap-3">
                {relatedRoutes.map((route) => (
                  <Link
                    key={route.slug}
                    href={`/trains/${route.slug}`}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    {route.label} →
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* CTA Box */}
          <div className="bg-green-50 border border-green-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Book Your Train Ticket
            </h3>
            <p className="text-gray-600 mb-4">
              Compare train schedules and prices for {originCity} to {destinationCity} route across booking platforms.
            </p>
            <Link
              href={searchUrl}
              className="inline-flex items-center px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors"
            >
              Compare Train Tickets
            </Link>
          </div>
        </div>
      </section>

      {/* Compliance Notice */}
      <section className="bg-gray-50 border-t border-gray-200 py-6">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs text-gray-500">
              Train fares and schedules are estimates provided by our travel partners and may vary. 
              TravelSearch is a metasearch engine - you'll complete your booking directly on IRCTC or partner websites.
              We may earn a commission when you book through our links.
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
