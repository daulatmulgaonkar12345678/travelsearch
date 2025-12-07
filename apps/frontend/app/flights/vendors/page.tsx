'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import { Plane, Clock, ArrowRight, Loader2, ExternalLink, Calendar, Users } from 'lucide-react'
import { FLIGHT_VENDORS } from '@/lib/vendors'
import { API_BASE_URL } from '@/lib/config'

function FlightVendorsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [redirecting, setRedirecting] = useState<string | null>(null)

  // Get offer details from URL params
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departureDate = searchParams.get('departure_date') || ''
  const returnDate = searchParams.get('return_date') || ''
  const airline = searchParams.get('airline') || ''
  const flightNumber = searchParams.get('flight_number') || ''
  const departureTime = searchParams.get('departure_time') || ''
  const arrivalTime = searchParams.get('arrival_time') || ''
  const price = searchParams.get('price') || '0'
  const currency = searchParams.get('currency') || 'INR'
  const stops = searchParams.get('stops') || '0'
  const adults = searchParams.get('adults') || '1'
  const children = searchParams.get('children') || '0'
  const infants = searchParams.get('infants') || '0'
  const cabinClass = searchParams.get('cabin_class') || 'economy'

  const handleVendorClick = async (vendorId: string) => {
    if (vendorId !== 'aviasales') {
      // Coming soon vendors
      alert(`${vendorId} integration coming soon!`)
      return
    }

    try {
      setRedirecting(vendorId)

      // Build redirect URL
      const redirectParams = new URLSearchParams({
        origin,
        destination,
        depart: departureDate,
        adults,
        children: children || '0',
        infants: infants || '0',
      })

      if (returnDate) {
        redirectParams.set('return', returnDate)
      }

      const redirectUrl = `${API_BASE_URL}/api/redirect/aviasales?${redirectParams.toString()}`

      // Open in new tab
      window.open(redirectUrl, '_blank')
    } catch (error) {
      console.error('Redirect error:', error)
      alert('Failed to redirect to vendor. Please try again.')
    } finally {
      setRedirecting(null)
    }
  }

  if (!origin || !destination) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-900 mb-2">Missing Flight Details</h3>
          <p className="text-yellow-700 mb-4">Unable to load flight information.</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
          >
            Back to Search
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Flight Details Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Selected Flight</h2>
        
        <div className="flex items-center justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">{origin}</div>
                <div className="text-sm text-gray-600">{departureTime}</div>
              </div>
              
              <div className="flex-1 px-4">
                <div className="flex items-center justify-center space-x-2 mb-2">
                  <div className="h-px flex-1 bg-gray-300"></div>
                  <Plane className="h-5 w-5 text-gray-400 transform rotate-90" />
                  <div className="h-px flex-1 bg-gray-300"></div>
                </div>
                <div className="text-center text-sm text-gray-600">
                  {stops === '0' ? 'Non-stop' : `${stops} stop(s)`}
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">{destination}</div>
                <div className="text-sm text-gray-600">{arrivalTime}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
          <div>
            <div className="text-sm text-gray-600 mb-1">Airline</div>
            <div className="font-semibold text-gray-900">{airline || 'Various'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Departure</div>
            <div className="font-semibold text-gray-900">{departureDate}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Passengers</div>
            <div className="font-semibold text-gray-900">
              {adults} Adult{parseInt(adults) > 1 ? 's' : ''}
              {parseInt(children) > 0 && `, ${children} Child`}
              {parseInt(infants) > 0 && `, ${infants} Infant`}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Class</div>
            <div className="font-semibold text-gray-900 capitalize">{cabinClass}</div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Total Price</div>
              <div className="text-3xl font-bold text-gray-900">
                {currency} {parseFloat(price).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Vendor Selection */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Choose Your Booking Platform</h3>
        <p className="text-gray-600 mb-6">
          Select a vendor to complete your booking. You'll be redirected to their website.
        </p>

        <div className="space-y-3">
          {FLIGHT_VENDORS.map((vendor) => {
            const isActive = vendor.type === 'real'
            const isRedirecting = redirecting === vendor.id

            return (
              <button
                key={vendor.id}
                onClick={() => handleVendorClick(vendor.id)}
                disabled={!isActive || isRedirecting}
                className={`
                  w-full p-4 rounded-lg border-2 transition-all text-left
                  ${isActive
                    ? 'border-blue-600 bg-blue-50 hover:bg-blue-100 cursor-pointer'
                    : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                  }
                  ${isRedirecting ? 'opacity-50' : ''}
                `}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div>
                        <div className="font-semibold text-gray-900">{vendor.name}</div>
                        <div className="text-sm text-gray-600">{vendor.description}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {isActive && (
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">
                          {currency} {parseFloat(price).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600">Same price</div>
                      </div>
                    )}
                    
                    {isRedirecting ? (
                      <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                    ) : isActive ? (
                      <div className="flex items-center space-x-2 text-blue-600">
                        <span className="font-semibold">Book Now</span>
                        <ExternalLink className="h-5 w-5" />
                      </div>
                    ) : (
                      <span className="text-sm font-semibold text-gray-500 px-3 py-1 bg-gray-200 rounded-full">
                        Coming Soon
                      </span>
                    )}
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-900">
            <strong>Note:</strong> You'll be redirected to the vendor's website to complete your booking. 
            Prices and availability are subject to change.
          </p>
        </div>
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:text-blue-700 font-semibold"
        >
          ← Back to Results
        </button>
      </div>
    </div>
  )
}

export default function FlightVendorsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
          </div>
        }>
          <FlightVendorsContent />
        </Suspense>
      </main>
    </div>
  )
}
