import SearchBarV2 from '@/components/search/SearchBarV2'
import { Plane, Hotel, Shield, TrendingDown } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Plane className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-display font-bold text-gray-900">TravelSearch</h1>
            </div>
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/flights" className="text-gray-600 hover:text-blue-600 transition-colors">Flights</a>
              <a href="/hotels" className="text-gray-600 hover:text-blue-600 transition-colors">Hotels</a>
              <a href="/admin" className="text-gray-600 hover:text-blue-600 transition-colors">Admin</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center mb-12">
          <h2 className="text-5xl md:text-6xl font-display font-bold text-gray-900 mb-6">
            Find Your Perfect Journey
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Compare flights and hotels from multiple providers. Get the best deals, instantly.
          </p>
        </div>

        {/* Search Component */}
        <div className="max-w-5xl mx-auto">
          <SearchBarV2 />
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="h-12 w-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
              <TrendingDown className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Best Prices</h3>
            <p className="text-gray-600">Compare prices from multiple providers to find the lowest fares</p>
          </div>
          
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="h-12 w-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">100% Transparent</h3>
            <p className="text-gray-600">No hidden fees. What you see is what you pay.</p>
          </div>
          
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="h-12 w-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Hotel className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Flights + Hotels</h3>
            <p className="text-gray-600">Book your entire trip in one place with confidence</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-gray-50 mt-16">
        <div className="container mx-auto px-4 py-8">
          <p className="text-center text-gray-600 text-sm">
            © 2025 TravelSearch. We compare, you save. Affiliate disclosure: We may earn commission from bookings.
          </p>
        </div>
      </footer>
    </div>
  )
}
