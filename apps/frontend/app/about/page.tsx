import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'
import { Plane, Search, DollarSign, Shield } from 'lucide-react'

export const metadata: Metadata = {
  title: 'About Us | TravelSearch',
  description: 'Learn about TravelSearch and how we help you find the best travel deals',
}

export default function About() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-16">
          <div className="container mx-auto px-4 max-w-4xl text-center">
            <h1 className="text-5xl font-bold mb-6">About TravelSearch</h1>
            <p className="text-xl text-gray-700 leading-relaxed">
              Your trusted travel meta-search platform for finding the best flight and hotel deals from multiple providers, all in one place.
            </p>
          </div>
        </section>

        {/* Mission Section */}
        <section className="container mx-auto px-4 py-16 max-w-4xl">
          <h2 className="text-3xl font-bold mb-8 text-center">Our Mission</h2>
          <p className="text-lg text-gray-700 leading-relaxed mb-6">
            TravelSearch was created with a simple goal: to make travel booking easier and more transparent. We believe travelers deserve access to comprehensive travel options without the hassle of visiting multiple booking sites.
          </p>
          <p className="text-lg text-gray-700 leading-relaxed">
            By aggregating results from numerous travel suppliers, we empower you to compare prices, schedules, and options quickly, helping you make informed decisions that best suit your travel needs and budget.
          </p>
        </section>

        {/* How It Works */}
        <section className="bg-gray-50 py-16">
          <div className="container mx-auto px-4 max-w-6xl">
            <h2 className="text-3xl font-bold mb-12 text-center">How TravelSearch Works</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Search</h3>
                <p className="text-gray-600 text-sm">
                  Enter your travel details - destination, dates, and preferences
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Plane className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Compare</h3>
                <p className="text-gray-600 text-sm">
                  View results from multiple travel suppliers side-by-side
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <DollarSign className="h-8 w-8 text-purple-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Choose</h3>
                <p className="text-gray-600 text-sm">
                  Select the best option based on price, schedule, and preferences
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="h-8 w-8 text-orange-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Book</h3>
                <p className="text-gray-600 text-sm">
                  Complete your booking directly with the chosen supplier
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* What We Do */}
        <section className="container mx-auto px-4 py-16 max-w-4xl">
          <h2 className="text-3xl font-bold mb-8 text-center">What We Offer</h2>
          <div className="space-y-6">
            <div className="border-l-4 border-blue-600 pl-6">
              <h3 className="font-semibold text-xl mb-2">Comprehensive Search</h3>
              <p className="text-gray-700">
                We aggregate flight and hotel options from multiple suppliers, giving you a wide range of choices in seconds.
              </p>
            </div>
            
            <div className="border-l-4 border-green-600 pl-6">
              <h3 className="font-semibold text-xl mb-2">Transparent Comparison</h3>
              <p className="text-gray-700">
                All prices are displayed clearly with no hidden fees. What you see is what you get from the supplier.
              </p>
            </div>
            
            <div className="border-l-4 border-purple-600 pl-6">
              <h3 className="font-semibold text-xl mb-2">Time-Saving Platform</h3>
              <p className="text-gray-700">
                No need to visit multiple booking sites. Get all the information you need in one convenient location.
              </p>
            </div>
            
            <div className="border-l-4 border-orange-600 pl-6">
              <h3 className="font-semibold text-xl mb-2">Independent Service</h3>
              <p className="text-gray-700">
                We're a meta-search platform, not a booking agent. We don't favor any particular supplier - we simply show you all available options.
              </p>
            </div>
          </div>
        </section>

        {/* Important Note */}
        <section className="bg-blue-50 py-12">
          <div className="container mx-auto px-4 max-w-4xl">
            <div className="bg-white rounded-lg shadow-md p-8">
              <h2 className="text-2xl font-bold mb-4">Important Information</h2>
              <p className="text-gray-700 mb-4">
                TravelSearch is a travel meta-search platform. We do not sell travel services directly. When you select a travel option, you will be directed to the supplier's website to complete your booking.
              </p>
              <p className="text-gray-700">
                All bookings are subject to the terms, conditions, and policies of the respective travel suppliers. Prices and availability may change between the time you search and when you complete your booking.
              </p>
            </div>
          </div>
        </section>

        {/* Contact CTA */}
        <section className="container mx-auto px-4 py-16 max-w-4xl text-center">
          <h2 className="text-3xl font-bold mb-6">Have Questions?</h2>
          <p className="text-lg text-gray-700 mb-8">
            We're here to help. If you have any questions about our platform or how to use it, don't hesitate to reach out.
          </p>
          <a 
            href="/contact" 
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Contact Us
          </a>
        </section>
      </main>
      <Footer />
    </div>
  )
}
