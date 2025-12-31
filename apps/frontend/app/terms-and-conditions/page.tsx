import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms and Conditions | TravelSearch',
  description: 'Terms and conditions for using TravelSearch',
}

export default function TermsAndConditions() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow container mx-auto px-4 py-12 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Terms and Conditions</h1>
        <div className="prose prose-lg max-w-none space-y-6">
          <p className="text-gray-600">
            <strong>Last Updated:</strong> December 2025
          </p>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing and using TravelSearch ("the Platform"), you accept and agree to be bound by these Terms and Conditions. If you do not agree with any part of these terms, please do not use our services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">2. Service Description</h2>
            <p>
              TravelSearch is a travel meta-search platform that aggregates and displays flight and hotel options from multiple third-party suppliers. We do not sell travel services directly. All bookings are made through the respective third-party suppliers.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">3. Third-Party Suppliers</h2>
            <p>
              When you select a travel option on our platform, you will be redirected to the third-party supplier's website to complete your booking. Your contractual relationship for the booking is directly with that supplier, not with TravelSearch. We are not responsible for:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>The accuracy of information provided by third-party suppliers</li>
              <li>The quality, availability, or delivery of travel services</li>
              <li>Any disputes arising from bookings made through third-party suppliers</li>
              <li>Pricing changes or errors on supplier websites</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">4. Price and Availability</h2>
            <p>
              All prices displayed on our platform are provided by third-party suppliers and are subject to change without notice. Final prices, availability, and booking terms are determined by the respective suppliers. We strive to display accurate information but cannot guarantee its completeness or accuracy.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">5. No Warranty</h2>
            <p>
              The Platform is provided "as is" without warranties of any kind, either express or implied. We do not warrant that:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>The service will be uninterrupted or error-free</li>
              <li>Results obtained from the Platform will be accurate or reliable</li>
              <li>Any errors in the Platform will be corrected</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">6. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, TravelSearch shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the Platform or any third-party services accessed through it.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">7. User Conduct</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the Platform for any unlawful purpose</li>
              <li>Attempt to gain unauthorized access to any part of the Platform</li>
              <li>Interfere with or disrupt the Platform's operation</li>
              <li>Use automated systems to access the Platform without permission</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">8. Intellectual Property</h2>
            <p>
              All content, trademarks, logos, and intellectual property on the Platform are owned by TravelSearch or its licensors. You may not reproduce, distribute, or create derivative works without express written permission.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">9. Modifications to Terms</h2>
            <p>
              We reserve the right to modify these Terms and Conditions at any time. Changes will be effective immediately upon posting. Your continued use of the Platform after any changes constitutes acceptance of the modified terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">10. Governing Law</h2>
            <p>
              These Terms and Conditions shall be governed by and construed in accordance with applicable laws, without regard to conflict of law provisions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">11. Contact Information</h2>
            <p>
              For questions about these Terms and Conditions, please contact us at:
              <br />
              <a href="mailto:legal@travelsearch.in" className="text-blue-600 hover:underline">
                legal@travelsearch.in
              </a>
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
