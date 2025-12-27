/**
 * SEO Route Page Template
 * 
 * Reusable template for static SEO-friendly flight route pages.
 * Each page includes:
 * - SEO-optimized H1 and meta tags
 * - Helpful, unique content (150-300 words)
 * - Embedded search bar with pre-filled route (UX improvement)
 * - Internal links to related routes
 * - CTA button to live search results
 * 
 * UX PRINCIPLE: User clicks route → everything auto-filled → adjust date → search
 */

'use client'

import { useState, useEffect } from 'react'
import { Metadata } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Calendar, Users, Search, ArrowRight } from 'lucide-react'
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
      description: `Compare flight prices from ${originCity} to ${destinationCity}. Search multiple providers instantly.`,
      type: 'website',
    },
  }
}

/**
 * Get tomorrow's date in YYYY-MM-DD format (default search date)
 */
function getTomorrowDate(): string {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  return date.toISOString().split('T')[0]
}

/**
 * Format date for display (Jan 15, 2025)
 */
function formatDisplayDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Embedded mini search bar for route pages
 * Pre-filled with route, user can adjust date and search
 */
function RouteSearchBar({
  originCode,
  originCity,
  destinationCode,
  destinationCity,
}: {
  originCode: string
  originCity: string
  destinationCode: string
  destinationCity: string
}) {
  const router = useRouter()
  const [departureDate, setDepartureDate] = useState(getTomorrowDate())
  const [adults, setAdults] = useState(1)
  const [isSearching, setIsSearching] = useState(false)

  // Get minimum date (today)
  const minDate = new Date().toISOString().split('T')[0]

  const handleSearch = () => {
    setIsSearching(true)
    
    const searchParams = new URLSearchParams({
      origin: originCode,
      destination: destinationCode,
      departure_date: departureDate,
      trip_type: 'oneway',
      adults: String(adults),
      cabin_class: 'economy',
    })
    
    router.push(`/flights/results?${searchParams.toString()}`)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
      {/* Route display (read-only) */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">From</p>
          <p className="font-semibold text-gray-900">{originCity}</p>
          <p className="text-sm text-gray-500">{originCode}</p>
        </div>
        
        <div className="flex-shrink-0">
          <ArrowRight className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="flex-1 bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">To</p>
          <p className="font-semibold text-gray-900">{destinationCity}</p>
          <p className="text-sm text-gray-500">{destinationCode}</p>
        </div>
      </div>

      {/* Editable fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {/* Date picker */}
        <div className="relative">
          <label className="block text-xs text-gray-500 mb-1">Departure Date</label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={departureDate}
              min={minDate}
              onChange={(e) => setDepartureDate(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Passengers */}
        <div className="relative">
          <label className="block text-xs text-gray-500 mb-1">Passengers</label>
          <div className="relative">
            <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={adults}
              onChange={(e) => setAdults(Number(e.target.value))}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => (
                <option key={n} value={n}>{n} {n === 1 ? 'Adult' : 'Adults'}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Search button */}
      <button
        onClick={handleSearch}
        disabled={isSearching}
        className="w-full py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:bg-blue-400"
      >
        {isSearching ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Searching...
          </>
        ) : (
          <>
            <Search className="w-5 h-5" />
            Search Flights
          </>
        )}
      </button>
      
      <p className="text-xs text-gray-500 text-center mt-3">
        Prices shown are sourced from our travel partners
      </p>
    </div>
  )
}

export default function RoutePageTemplate({
  originCity,
  originCode,
  destinationCity,
  destinationCode,
  content,
  relatedRoutes,
}: RoutePageProps) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

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

            {/* Embedded Search Bar - Only render after mount to avoid hydration issues */}
            {mounted && (
              <div className="max-w-xl mx-auto">
                <RouteSearchBar
                  originCode={originCode}
                  originCity={originCity}
                  destinationCode={destinationCode}
                  destinationCity={destinationCity}
                />
              </div>
            )}
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
