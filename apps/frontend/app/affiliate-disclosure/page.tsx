import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Affiliate Disclosure | TravelSearch',
  description: 'Transparent disclosure of affiliate relationships and commission structure.',
}

export default function AffiliateDisclosure() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow container mx-auto px-4 py-12 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Affiliate Disclosure</h1>
        
        <div className="prose prose-lg max-w-none space-y-6">
          <p className="text-lg text-gray-700">
            <strong>Last Updated:</strong> December 2025
          </p>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">How TravelSearch Operates</h2>
            <p>
              TravelSearch is a flight comparison platform that earns revenue through affiliate 
              partnerships with airlines, online travel agencies, and booking providers. This page 
              explains our business model transparently.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Affiliate Commissions</h2>
            <p>
              When you click on a flight result and proceed to book on a partner's website, we may 
              receive a commission if you complete a booking. This commission is paid by the partner—not 
              by you. The price you pay is the same whether you arrive at the booking site through 
              TravelSearch or directly.
            </p>
            <p>
              <strong>Important:</strong> Affiliate commissions do not increase your ticket price. 
              Partners pay us a referral fee as part of their customer acquisition costs.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Partner Relationships</h2>
            <p>
              We maintain affiliate relationships with numerous airlines and booking platforms. These 
              relationships allow us to display real-time flight data and direct you to booking pages. 
              Our partnerships are disclosed here in the interest of transparency.
            </p>
            <p>
              We do not operate our own booking system. All transactions occur on the partner's secure 
              website, subject to their terms, conditions, and privacy policies.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Search Result Ranking</h2>
            <p>
              Flight results are displayed based on relevance to your search query. Default sorting 
              typically prioritizes factors like:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Best overall value (price, duration, convenience)</li>
              <li>Lowest price</li>
              <li>Shortest duration</li>
              <li>Earliest or most convenient departure times</li>
            </ul>
            <p>
              We do not prioritize results based on which partner pays higher commissions. Users can 
              sort and filter results according to their preferences.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Independence and Objectivity</h2>
            <p>
              While we earn revenue through affiliate commissions, our goal is to provide an unbiased 
              comparison tool. We display options from multiple providers so you can make informed 
              decisions based on your priorities—whether that's price, schedule, airline preference, 
              or other factors.
            </p>
            <p>
              TravelSearch does not receive payments to display or prioritize specific flights in 
              search results. Commission structures vary by partner but do not influence ranking algorithms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">What We Do NOT Do</h2>
            <p>
              To maintain clarity:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>We do not markup prices</li>
              <li>We do not hide the lowest-priced options</li>
              <li>We do not accept payment for preferential ranking</li>
              <li>We do not guarantee "lowest prices" (we display comparative data)</li>
              <li>We do not handle bookings or customer service for partners</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Types of Partners</h2>
            <p>
              Our affiliate network includes:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Airlines:</strong> Direct booking through airline websites</li>
              <li><strong>Online Travel Agencies (OTAs):</strong> Third-party booking platforms</li>
              <li><strong>Aggregator Networks:</strong> Technology providers aggregating flight data</li>
            </ul>
            <p>
              Each partner operates independently. TravelSearch is not responsible for their pricing, 
              customer service, cancellation policies, or booking fulfillment.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Regulatory Compliance</h2>
            <p>
              This disclosure complies with consumer protection and advertising standards globally, 
              including FTC guidelines (United States), ASA guidelines (United Kingdom), and similar 
              frameworks worldwide. We believe transparent disclosure builds trust.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mt-8 mb-4">Questions?</h2>
            <p>
              If you have questions about our affiliate relationships or business model, contact us at:
              <br />
              <a href="mailto:admin@travelsearch.in" className="text-blue-600 hover:underline">
                admin@travelsearch.in
              </a>
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
