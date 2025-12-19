import SearchBarV3 from '@/components/search/SearchBarV3'
import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hotel Search | TravelSearch',
  description: 'Search and compare hotel prices from multiple providers',
}

export default function HotelsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Navigation />

      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center mb-12">
          <h2 className="text-5xl md:text-6xl font-display font-bold text-gray-900 mb-6">
            Find Your Perfect Stay
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Compare hotel prices from multiple providers. Book with confidence.
          </p>
        </div>

        <div className="max-w-5xl mx-auto">
          <SearchBarV3 defaultTab="hotels" />
        </div>
      </section>

      <Footer />
    </div>
  )
}
