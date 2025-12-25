import SearchBarV3 from '@/components/search/SearchBarV3'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import TrustStrip from '@/components/trust/TrustStrip'
import RecentSearches from '@/components/features/RecentSearches'
import { PopularFlightRoutes, PopularHotelDestinations } from '@/components/seo/InternalLinks'
import { Hotel, Shield, TrendingDown } from 'lucide-react'

export default function Home() {
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
            Compare flights and hotels from multiple providers. Search options instantly.
          </p>
        </div>

        {/* Search Component */}
        <div className="max-w-5xl mx-auto space-y-4">
          <SearchBarV3 />
          
          {/* Trust Strip - appears below search */}
          <TrustStrip />
          
          {/* Recent Searches - shows last 3 saved searches */}
          <div className="pt-2">
            <RecentSearches />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="h-12 w-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
              <TrendingDown className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Compare Prices</h3>
            <p className="text-gray-600">Search across multiple providers to compare fares and options</p>
          </div>
          
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="h-12 w-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Transparent Pricing</h3>
            <p className="text-gray-600">Prices shown are from our travel partners. No hidden fees.</p>
          </div>
          
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="h-12 w-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Hotel className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Flights + Hotels</h3>
            <p className="text-gray-600">Compare options for your entire trip in one place</p>
          </div>
        </div>
      </section>

      {/* Internal Links for SEO */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          <PopularFlightRoutes />
          <PopularHotelDestinations />
        </div>
      </section>

      <Footer />
    </div>
  )
}
