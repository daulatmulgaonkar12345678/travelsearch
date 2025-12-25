import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About TravelSearch | Independent Flight Comparison Platform',
  description: 'Learn about TravelSearch - an independent flight comparison platform helping travelers find and compare options from multiple providers.',
}

export default function AboutUs() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow container mx-auto px-4 py-12 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">About TravelSearch</h1>
        
        <div className="prose prose-lg max-w-none space-y-6">
          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Who We Are</h2>
            <p>
              TravelSearch is an independent flight comparison platform designed to help travelers 
              make informed decisions. We aggregate real-time flight data from multiple airlines 
              and booking providers, displaying options side-by-side for easy comparison.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">What We Do</h2>
            <p>
              Our platform searches across numerous travel providers to present you with available 
              flight options, including pricing, departure times, duration, and routing information. 
              We organize this data in a clear, filterable format so you can quickly identify flights 
              that match your preferences.
            </p>
            <p>
              <strong>Important:</strong> TravelSearch does not sell tickets, process payments, or 
              issue bookings. We are a comparison tool only. When you select a flight, you will be 
              directed to the airline or booking provider's website to complete your purchase directly 
              with them.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">How We Operate</h2>
            <p>
              TravelSearch operates as an independent technology platform. We maintain partnerships 
              with various airlines, online travel agencies, and booking providers. When you click 
              through to book a flight, we may receive a commission from the partner. This commission 
              does not affect the price you pay—it is paid by the partner as a referral fee.
            </p>
            <p>
              Our search results display flights based on relevance to your query, sorted by factors 
              like price, duration, or departure time. We do not prioritize results based on commission 
              rates or paid placements.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Our Commitment</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>Display transparent, real-time flight information</li>
              <li>Provide fast, reliable search functionality</li>
              <li>Maintain user-first design principles</li>
              <li>Clearly disclose our affiliate relationships</li>
              <li>Never hide fees or mislead users</li>
              <li>Respect user privacy and data protection standards</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">What We Are Not</h2>
            <p>
              TravelSearch is not a travel agency, airline, or booking agent. We do not:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Sell tickets or process bookings</li>
              <li>Handle customer service for bookings made through partners</li>
              <li>Control pricing or availability</li>
              <li>Issue refunds or manage cancellations</li>
              <li>Act as a party to your contract with travel providers</li>
            </ul>
            <p>
              All bookings are contractual agreements between you and the airline or booking provider. 
              For support related to your booking, please contact the provider directly.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Technology & Data</h2>
            <p>
              Our platform uses modern search infrastructure to query multiple data sources simultaneously, 
              delivering results in seconds. Flight information, including prices and availability, is 
              provided by our partner networks and is subject to change. We strive for accuracy but 
              cannot guarantee real-time synchronization across all providers.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Contact Us</h2>
            <p>
              For questions about our platform, partnership inquiries, or general feedback:
              <br />
              <a href="mailto:hello@travelsearch.com" className="text-blue-600 hover:underline">
                hello@travelsearch.com
              </a>
            </p>
            <p className="text-sm text-gray-600 mt-4">
              For booking-related issues, please contact your airline or booking provider directly.
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
