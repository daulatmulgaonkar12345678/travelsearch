import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import { Metadata } from 'next'
import { Mail, MessageCircle, HelpCircle } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Contact Us | TravelSearch',
  description: 'Get in touch with TravelSearch',
}

export default function Contact() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 to-indigo-100 py-16">
          <div className="container mx-auto px-4 max-w-4xl text-center">
            <h1 className="text-5xl font-bold mb-6">Contact Us</h1>
            <p className="text-xl text-gray-700 leading-relaxed">
              Have a question or need assistance? We're here to help.
            </p>
          </div>
        </section>

        {/* Contact Methods */}
        <section className="container mx-auto px-4 py-16 max-w-5xl">
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mail className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="font-semibold text-lg mb-2">General Inquiries</h3>
              <p className="text-gray-600 text-sm mb-2">For general questions about our platform</p>
              <a href="mailto:info@travelsearch.in" className="text-blue-600 hover:underline">
                info@travelsearch.in
              </a>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <HelpCircle className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Support</h3>
              <p className="text-gray-600 text-sm mb-2">Need help using our platform?</p>
              <a href="mailto:support@travelsearch.in" className="text-blue-600 hover:underline">
                support@travelsearch.in
              </a>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="font-semibold text-lg mb-2">Feedback</h3>
              <p className="text-gray-600 text-sm mb-2">Share your suggestions with us</p>
              <a href="mailto:feedback@travelsearch.in" className="text-blue-600 hover:underline">
                feedback@travelsearch.in
              </a>
            </div>
          </div>

          {/* Important Notice */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-r-lg">
            <h3 className="font-semibold text-lg mb-2 text-yellow-900">Important Notice</h3>
            <p className="text-yellow-800 text-sm">
              <strong>For booking-related inquiries:</strong> If you have questions about a specific booking, cancellation, or refund, please contact the travel supplier directly. TravelSearch is a meta-search platform and does not process bookings or handle customer service for travel suppliers.
            </p>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="bg-gray-50 py-16">
          <div className="container mx-auto px-4 max-w-4xl">
            <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-2">What is TravelSearch?</h3>
                <p className="text-gray-700">
                  TravelSearch is a travel meta-search platform that helps you compare flights and hotels from multiple suppliers in one place. We don't sell travel services directly but help you find the best options.
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-2">How do I book travel through TravelSearch?</h3>
                <p className="text-gray-700">
                  Search for your desired travel options on our platform. When you find an option you like, click the booking button to be redirected to the supplier's website where you can complete your booking.
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-2">Are the prices I see the final prices?</h3>
                <p className="text-gray-700">
                  Prices displayed are provided by travel suppliers and are subject to change. The final price will be confirmed by the supplier at the time of booking. We recommend completing your booking promptly to secure the displayed price.
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-2">Can I cancel or modify my booking through TravelSearch?</h3>
                <p className="text-gray-700">
                  No, all cancellations and modifications must be made directly with the travel supplier where you completed your booking. Each supplier has their own cancellation and modification policies.
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-2">Is my information secure?</h3>
                <p className="text-gray-700">
                  Yes, we take your privacy seriously. We use industry-standard security measures to protect your data. For more information, please read our Privacy Policy.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Response Time Notice */}
        <section className="container mx-auto px-4 py-12 max-w-4xl text-center">
          <div className="bg-blue-50 rounded-lg p-8">
            <h3 className="text-xl font-semibold mb-4">Response Time</h3>
            <p className="text-gray-700">
              We aim to respond to all inquiries within 24-48 hours during business days. Thank you for your patience.
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
