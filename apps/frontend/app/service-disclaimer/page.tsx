import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Service Disclaimer | TravelSearch',
  description: 'Important information about TravelSearch service limitations and third-party relationships.',
}

export default function ServiceDisclaimer() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow container mx-auto px-4 py-12 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Service Disclaimer</h1>
        
        <div className="prose prose-lg max-w-none space-y-6">
          <p className="text-lg text-gray-700">
            <strong>Last Updated:</strong> December 2025
          </p>

          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 my-6">
            <p className="font-semibold text-gray-900 mb-2">Important Notice</p>
            <p className="text-gray-800">
              TravelSearch is a flight comparison platform, not a travel agency or booking agent. 
              We do not sell tickets, process payments, or handle bookings. All transactions occur 
              directly between you and the airline or booking provider.
            </p>
          </div>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Nature of Service</h2>
            <p>
              TravelSearch provides technology infrastructure that aggregates and displays flight 
              information from multiple sources. Our role is limited to:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Searching and displaying available flight options</li>
              <li>Comparing data from multiple providers</li>
              <li>Redirecting users to booking partner websites</li>
            </ul>
            <p>
              We are not party to any transaction you complete with airlines or booking providers.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Data Accuracy</h2>
            <p>
              Flight information displayed on TravelSearch, including prices, availability, schedules, 
              and routing, is provided by third-party data sources. While we strive for accuracy:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Prices may change between search and booking</li>
              <li>Availability is subject to real-time inventory changes</li>
              <li>Flight schedules may be modified by airlines</li>
              <li>We cannot guarantee synchronization across all data sources</li>
            </ul>
            <p>
              <strong>Final prices, availability, and terms are determined by the booking provider.</strong>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Third-Party Relationships</h2>
            <p>
              When you click through to book a flight, you are entering into a contractual relationship 
              with that airline or booking provider. TravelSearch:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Does not control their pricing or policies</li>
              <li>Does not verify the accuracy of their data</li>
              <li>Is not responsible for booking fulfillment</li>
              <li>Cannot process refunds or changes on their behalf</li>
              <li>Does not provide customer support for completed bookings</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">No Warranties</h2>
            <p>
              TravelSearch is provided "as is" without warranties of any kind. We do not warrant that:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Flight information will be error-free or always current</li>
              <li>The service will be uninterrupted or available at all times</li>
              <li>All flight options are displayed (coverage depends on partner agreements)</li>
              <li>Displayed flights will be available when you attempt to book</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Limitation of Liability</h2>
            <p>
              TravelSearch is not liable for:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Losses arising from booking through partner websites</li>
              <li>Flight delays, cancellations, or schedule changes</li>
              <li>Price increases between search and booking</li>
              <li>Errors in third-party data</li>
              <li>Issues with partner booking systems</li>
              <li>Disputes with airlines or booking providers</li>
            </ul>
            <p>
              Your recourse for booking-related issues is directly with the airline or booking provider.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">User Responsibilities</h2>
            <p>
              When using TravelSearch, you are responsible for:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Verifying prices and availability before booking</li>
              <li>Reading and accepting partner terms and conditions</li>
              <li>Ensuring you have required travel documents</li>
              <li>Understanding cancellation and change policies</li>
              <li>Contacting partners directly for booking support</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Booking Recommendations</h2>
            <p>
              Before completing any booking:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Carefully review flight details, dates, and passenger names</li>
              <li>Understand baggage allowances and restrictions</li>
              <li>Check cancellation and change policies</li>
              <li>Verify passport and visa requirements</li>
              <li>Consider purchasing travel insurance</li>
              <li>Save booking confirmation emails</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">No Professional Advice</h2>
            <p>
              Information on TravelSearch is for general informational purposes only. We do not provide:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Travel advice or recommendations</li>
              <li>Health or safety guidance</li>
              <li>Visa or documentation assistance</li>
              <li>Legal or financial advice</li>
            </ul>
            <p>
              Consult qualified professionals for travel-related advice.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Force Majeure</h2>
            <p>
              TravelSearch is not responsible for service disruptions caused by events beyond our 
              control, including but not limited to: natural disasters, pandemics, government actions, 
              technical failures, or partner system outages.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Changes to This Disclaimer</h2>
            <p>
              We may update this disclaimer periodically. Continued use of TravelSearch after changes 
              constitutes acceptance of the modified disclaimer.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Questions or Issues</h2>
            <p>
              For platform-related questions:
              <br />
              <a href="mailto:support@travelsearch.com" className="text-blue-600 hover:underline">
                support@travelsearch.com
              </a>
            </p>
            <p className="text-sm text-gray-600 mt-4">
              <strong>For booking-related issues, contact your airline or booking provider directly.</strong>
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
