import SearchBarV2 from '@/components/search/SearchBarV2'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hotel Search | TravelSearch',
  description: 'Search and compare hotel prices from multiple providers',
}

export default function HotelsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center space-x-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-8 w-8 text-blue-600">
                <path d="M18 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2Z"/>
                <path d="m9 16 .348-.24c1.465-1.013 3.84-1.013 5.304 0L15 16"/>
                <path d="M8 7h.01"/><path d="M16 7h.01"/><path d="M12 7h.01"/>
                <path d="M12 11h.01"/><path d="M16 11h.01"/><path d="M8 11h.01"/>
                <path d="M10 22v-6.5m4 0V22"/>
              </svg>
              <h1 className="text-2xl font-display font-bold text-gray-900">TravelSearch</h1>
            </a>
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/flights" className="text-gray-600 hover:text-blue-600 transition-colors">Flights</a>
              <a href="/hotels" className="text-blue-600 font-semibold">Hotels</a>
              <a href="/admin" className="text-gray-600 hover:text-blue-600 transition-colors">Admin</a>
            </nav>
          </div>
        </div>
      </header>

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
          <SearchBarV2 defaultTab="hotels" />
        </div>
      </section>

      <footer className="border-t bg-gray-50 mt-16">
        <div className="container mx-auto px-4 py-8">
          <p className="text-center text-gray-600 text-sm">
            © 2025 TravelSearch. We compare, you save.
          </p>
        </div>
      </footer>
    </div>
  )
}
