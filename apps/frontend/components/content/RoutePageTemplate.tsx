/**
 * Static Route Page Content Generator
 * Template for SEO-optimized city-pair pages
 */

import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'
import Link from 'next/link'

interface RoutePageProps {
  params: {
    originCity: string
    destinationCity: string
    originCode: string
    destinationCode: string
  }
}

export async function generateMetadata({ params }: RoutePageProps): Promise<Metadata> {
  const { originCity, destinationCity } = params
  
  return {
    title: `Flights from ${originCity} to ${destinationCity} | Compare & Book | TravelSearch`,
    description: `Compare flights from ${originCity} to ${destinationCity}. View multiple airlines, departure times, and prices. Find the best flight option for your travel dates.`,
    openGraph: {
      title: `${originCity} to ${destinationCity} Flights`,
      description: `Compare all available flights and book your journey with confidence.`,
    }
  }
}

export default function RoutePageTemplate({ params }: RoutePageProps) {
  const { originCity, destinationCity, originCode, destinationCode } = params
  
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navigation />
      
      <main className="flex-grow container mx-auto px-4 py-12 max-w-4xl">
        {/* Breadcrumb */}
        <nav className="text-sm text-gray-600 mb-6">
          <Link href="/" className="hover:text-blue-600">Home</Link>
          <span className="mx-2">/</span>
          <span>Flights {originCity} to {destinationCity}</span>
        </nav>

        {/* Main Heading */}
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          Flights from {originCity} to {destinationCity}
        </h1>

        {/* Route Overview Content */}
        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Route Overview</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              The {originCity} ({originCode}) to {destinationCity} ({destinationCode}) route is 
              served by multiple airlines operating direct and connecting flights throughout the week. 
              Flight availability, pricing, and departure times vary based on season, day of the week, 
              and booking timing. Comparing options across different providers helps identify flights 
              that match your schedule and budget.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Why Compare Flight Options?</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              Airlines and booking platforms offer different fares, departure times, and connection 
              options for the same route. Some flights may offer morning departures, while others 
              provide evening or red-eye options. Flight duration can also vary significantly 
              depending on whether you choose direct flights or connections through hub airports. 
              By viewing multiple options simultaneously, you can evaluate trade-offs between price, 
              convenience, and travel time without visiting multiple websites.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Typical Travel Patterns</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              This route typically sees varied demand across different times of the year. Business 
              travelers often prefer morning departures for same-day meetings, while leisure travelers 
              may opt for weekend flights. Peak travel periods may experience higher demand and 
              different availability patterns. Our platform aggregates real-time data, showing you 
              current options and allowing you to filter by departure time, duration, stops, and 
              other preferences.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">How TravelSearch Helps</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              Instead of checking multiple airline and booking websites individually, TravelSearch 
              displays available flights from various sources in one place. You can sort by price, 
              duration, or departure time, and compare details side-by-side. Once you've identified 
              your preferred flight, you'll be directed to complete your booking directly with the 
              airline or travel provider's secure website. We don't handle payments or issue tickets—our 
              role is to help you find and compare options efficiently.
            </p>
          </section>

          {/* Call to Action */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-8 text-center mt-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Ready to Compare Flights?
            </h3>
            <p className="text-gray-700 mb-6">
              Search for available flights from {originCity} to {destinationCity} and compare 
              options from multiple providers.
            </p>
            <Link 
              href={`/?origin=${originCode}&destination=${destinationCode}`}
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-lg transition-colors shadow-lg hover:shadow-xl"
            >
              Search Flights {originCity} → {destinationCity}
            </Link>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  )
}
