import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Disclaimer | TravelSearch',
  description: 'Important disclaimers about our service',
}

export default function Disclaimer() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow container mx-auto px-4 py-12 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Disclaimer</h1>
        <div className="prose prose-lg max-w-none space-y-6">
          <p className="text-gray-600">
            <strong>Last Updated:</strong> December 2025
          </p>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">1. Nature of Service</h2>
            <p>
              TravelSearch is a travel meta-search platform that aggregates and displays travel options from multiple third-party suppliers. We are not a travel agency, tour operator, or booking agent. We do not provide travel services directly.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">2. Third-Party Information</h2>
            <p>
              All flight and hotel information, including prices, availability, schedules, and terms, are provided by third-party suppliers. We display this information as received but do not:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Guarantee the accuracy or completeness of any information</li>
              <li>Verify the quality or suitability of travel services</li>
              <li>Control pricing or availability of travel options</li>
              <li>Maintain real-time synchronization with all suppliers</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">3. Price and Availability Disclaimer</h2>
            <p>
              Prices and availability displayed on TravelSearch are subject to change without notice. The final price you pay will be determined by the third-party supplier at the time of booking. We are not responsible for:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Price increases between search and booking</li>
              <li>Sold-out inventory shown as available</li>
              <li>Currency conversion rates or fees</li>
              <li>Additional taxes, fees, or charges imposed by suppliers</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">4. Booking and Cancellation</h2>
            <p>
              All bookings are made directly with third-party suppliers. Each supplier has its own booking, cancellation, and refund policies. TravelSearch does not process bookings, collect payments, or handle cancellations. Please review the supplier's terms and conditions before completing any booking.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">5. No Responsibility for Third-Party Services</h2>
            <p>
              TravelSearch is not responsible for:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>The quality, safety, or legality of travel services provided by suppliers</li>
              <li>Flight delays, cancellations, or schedule changes</li>
              <li>Hotel overbooking, service quality, or facility conditions</li>
              <li>Acts of God, weather conditions, or force majeure events</li>
              <li>Lost, stolen, or damaged property during travel</li>
              <li>Medical emergencies or health issues during travel</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">6. Travel Documentation</h2>
            <p>
              It is your responsibility to ensure you have all necessary travel documents, including passports, visas, vaccinations, and travel insurance. TravelSearch provides no advice regarding travel documentation requirements.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">7. External Links</h2>
            <p>
              Our platform contains links to third-party websites. We have no control over the content, privacy policies, or practices of these sites and assume no responsibility for them. Accessing third-party websites is at your own risk.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">8. Technical Limitations</h2>
            <p>
              While we strive to maintain platform availability, we do not guarantee uninterrupted service. Technical issues, maintenance, or factors beyond our control may affect platform performance or availability.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">9. No Professional Advice</h2>
            <p>
              Information on TravelSearch is for general informational purposes only and should not be considered professional travel advice. We recommend consulting with qualified travel professionals for specific travel planning needs.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">10. Changes to Disclaimer</h2>
            <p>
              We reserve the right to modify this disclaimer at any time. Changes will be effective immediately upon posting. Your continued use of the platform constitutes acceptance of any modifications.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">11. Contact Us</h2>
            <p>
              If you have questions about this disclaimer, please contact us at:
              <br />
              <a href="mailto:info@travelsearch.in" className="text-blue-600 hover:underline">
                info@travelsearch.in
              </a>
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
