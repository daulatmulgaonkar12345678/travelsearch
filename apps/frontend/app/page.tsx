'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import SearchBarV3 from '@/components/search/SearchBarV3'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import TrustStrip from '@/components/trust/TrustStrip'
import RecentSearches from '@/components/features/RecentSearches'
import { PopularFlightRoutes, PopularHotelDestinations, PopularTrainRoutes, PopularBusRoutes } from '@/components/seo/InternalLinks'
import { Hotel, Shield, TrendingDown, Train, Bus, Plane, Loader2 } from 'lucide-react'

type ServiceType = 'flights' | 'trains' | 'buses' | 'hotels'

/**
 * Service-Aware Popular Sections
 * Shows different popular routes/destinations based on active service
 */
function PopularSections({ activeService }: { activeService: ServiceType }) {
  switch (activeService) {
    case 'flights':
      return <PopularFlightRoutes />
    case 'trains':
      return <PopularTrainRoutes />
    case 'buses':
      return <PopularBusRoutes />
    case 'hotels':
      return <PopularHotelDestinations />
    default:
      return <PopularFlightRoutes />
  }
}

/**
 * Service-Aware Feature Cards
 * Highlights relevant features based on active service
 */
function FeatureCards({ activeService }: { activeService: ServiceType }) {
  const features = {
    flights: [
      { icon: TrendingDown, color: 'blue', title: 'Compare Flight Prices', description: 'Search across multiple airlines to compare fares and options' },
      { icon: Shield, color: 'green', title: 'Transparent Pricing', description: 'Prices shown are from our travel partners. No hidden fees.' },
      { icon: Hotel, color: 'purple', title: 'Flights + Hotels', description: 'Compare options for your entire trip in one place' },
    ],
    trains: [
      { icon: Train, color: 'blue', title: 'Compare Train Options', description: 'Search across Indian Railways routes and classes' },
      { icon: Shield, color: 'green', title: 'Official Partners', description: 'Book via IRCTC, ixigo, Paytm and trusted partners' },
      { icon: TrendingDown, color: 'purple', title: 'Fare Estimates', description: 'View estimated fares across different train classes' },
    ],
    buses: [
      { icon: Bus, color: 'orange', title: 'Compare Bus Options', description: 'Search AC, sleeper, and seater buses across operators' },
      { icon: Shield, color: 'green', title: 'Trusted Operators', description: 'Book via redBus, AbhiBus, Paytm and more' },
      { icon: TrendingDown, color: 'purple', title: 'Best Prices', description: 'Compare fares from multiple bus operators' },
    ],
    hotels: [
      { icon: Hotel, color: 'indigo', title: 'Compare Hotels', description: 'Search hotels across multiple booking platforms' },
      { icon: Shield, color: 'green', title: 'Verified Partners', description: 'Book via trusted hotel booking sites' },
      { icon: TrendingDown, color: 'purple', title: 'Price Comparison', description: 'Find the best rates for your stay' },
    ],
  }

  const colorClasses: Record<string, { bg: string; text: string }> = {
    blue: { bg: 'bg-blue-100', text: 'text-blue-600' },
    green: { bg: 'bg-green-100', text: 'text-green-600' },
    purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
    orange: { bg: 'bg-orange-100', text: 'text-orange-600' },
    indigo: { bg: 'bg-indigo-100', text: 'text-indigo-600' },
  }

  const currentFeatures = features[activeService] || features.flights

  return (
    <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
      {currentFeatures.map((feature, idx) => {
        const Icon = feature.icon
        const colors = colorClasses[feature.color] || colorClasses.blue
        return (
          <div key={idx} className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className={`h-12 w-12 ${colors.bg} rounded-xl flex items-center justify-center mb-4`}>
              <Icon className={`h-6 w-6 ${colors.text}`} />
            </div>
            <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
            <p className="text-gray-600">{feature.description}</p>
          </div>
        )
      })}
    </div>
  )
}

export default function Home() {
  const searchParams = useSearchParams()
  
  // Get active service from URL - single source of truth
  const tabParam = searchParams.get('tab') as ServiceType | null
  const activeService: ServiceType = (tabParam && ['flights', 'trains', 'buses', 'hotels'].includes(tabParam)) 
    ? tabParam 
    : 'flights'
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navigation />

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-display font-bold text-gray-900 mb-6">
            Find Your Perfect Journey
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Compare flights, trains, buses, and hotels from multiple providers. Search options instantly.
          </p>
        </div>

        {/* Search Component */}
        <div className="max-w-5xl mx-auto space-y-4">
          <SearchBarV3 defaultTab={activeService} />
          
          {/* Trust Strip - appears below search */}
          <TrustStrip />
          
          {/* Recent Searches - filtered by active service */}
          <div className="pt-2">
            <RecentSearches activeService={activeService} />
          </div>
        </div>
      </section>

      {/* Features - service-aware */}
      <section className="container mx-auto px-4 py-16">
        <FeatureCards activeService={activeService} />
      </section>

      {/* Popular Routes & Destinations - service-aware */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-5xl mx-auto space-y-12">
          <PopularSections activeService={activeService} />
        </div>
      </section>

      <Footer />
    </div>
  )
}
